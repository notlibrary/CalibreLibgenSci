#!/usr/bin/env python3
import random
import math

from random import randint
from time import sleep
from multiprocessing.pool import ThreadPool

from lxml import etree

import urllib.request, urllib.parse, urllib.error
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import parse_qs

def fetch_url(url):
    retries = 5
    while retries:
        try:
            response = urlopen(url)
            return url, response.read(), None
        except urllib.error.HTTPError as e:
            if e.code == 503:
                sleep( randint(50,200)/1000.0) 
                retries -= 1
                continue
            return url, None, e
    return url, None, urllib.error.HTTPError   
    
def scrap_download_link(md5):
    necronomicon_url = 'http://31.42.184.140/main/268000/ad68152110bfd420c962911da22c2a14/AD68152110BFD420C962911DA22C2A14.pdf'
    download_urls = [
        'http://library.lol/main/{}'.format(md5),
        'http://library.lol/main/{}&open=2'.format(md5),
        'http://library.lol/main/{}&open=1'.format(md5),
        'https://3lib.net/md5/{}&open=2'.format(md5),
        'http://bookfi.net/md5/{}&open=2'.format(md5),
    ]
    for url in download_urls:
        try:
            final_link = fetch_url(url)
            
            if not final_link:
                continue
            md5t = md5,
            return final_link + md5t
        except urllib.error.HTTPError as e:
            continue
            
    return necronomicon_url, None, e, md5

def xpath(node, path):
    tree = node.getroottree()
    base_xpath = tree.getpath(node)

    return tree.xpath(base_xpath + path)

class LibgenMirror:
    def __init__(self, url, file_extension, size, unit):
        self.url = url
        self.file_extension = file_extension
        self.size = size
        self.unit = unit

    @staticmethod
    def parse(node, file_extension, file_size, file_size_unit):
        url = node.get('href')

        return LibgenMirror(url, file_extension, file_size, file_size_unit)

class LibgenBook:
    def __init__(self, libid, authors, title, series, publisher, year , pages, language, file_size, file_extension, mirrors, md5, image_url, poffset):
        self.libid = libid
        self.authors = authors
        self.title = title
        self.series = series
        self.publisher = publisher
        self.year = year
        self.pages = pages
        self.language = language
        self.file_size = file_size
        self.file_extension = file_extension
        self.mirrors = mirrors
        self.md5 = md5
        self.image_url = image_url
        self.poffset = poffset
        
    @staticmethod
    def parse(node, orig_page):
        LIBID_XPATH='/td[1]'
        AUTHOR_XPATH = '/td[2]//a'
        TITLE_XPATH = "/td[3]/a[@id="
        SERIES_XPATH = "/td[3]//i"
        PUBLISHER_XPATH = '/td[4]'
        YEAR_XPATH = '/td[5]'
        PAGES_XPATH = '/td[6]'
        LANGUAGE_XPATH = '/td[7]'
        FILE_SIZE_XPATH = '/td[8]'
        EXTENSION_XPATH = '/td[9]'
        MIRRORS_XPATH = '/td[10]//a'

        libid = xpath(node, LIBID_XPATH)[0].text
        TITLE_XPATH = TITLE_XPATH + libid + "]"
        
        # Parse the Author(s) column into `authors`
        authors = ''
        authors_node = xpath(node, AUTHOR_XPATH)
        if authors_node[0].text and authors_node[-1].text:
            authors = ' & '.join([ author.text for author in authors_node ])

        if len(authors) == 0:
            authors = 'Unknown'

        title = xpath(node, TITLE_XPATH)[0].text
        series_list = xpath(node, SERIES_XPATH)
        series = " "
        if series_list:
            series = series_list[0].text
        
        
        publisher = xpath(node, PUBLISHER_XPATH)[0].text
        year = xpath(node, YEAR_XPATH)[0].text
        pages = xpath(node, PAGES_XPATH)[0].text
        language = xpath(node, LANGUAGE_XPATH)[0].text 
        file_size_str = xpath(node, FILE_SIZE_XPATH)[0].text
        file_size_str = file_size_str.split()
        
        file_size = file_size_str[0]
        file_size_unit = file_size_str[1]


        file_extension = xpath(node, EXTENSION_XPATH)[0].text
        mirrors = [
            LibgenMirror.parse(n, file_extension, file_size, file_size_unit)
            for n in xpath(node, MIRRORS_XPATH)
        ]

        md5_text = xpath(node, TITLE_XPATH)[0].get('href')
        parsed_md5=urlparse(md5_text)
        md5 = parse_qs(parsed_md5.query)['md5'][0]
        poffset = orig_page
        if not authors or not title:
            return None

        return LibgenBook(libid, authors, title, series, publisher, year , pages, language, file_size, file_extension, mirrors, md5,  None, poffset)


class LibgenSearchResults:
    results = []
    def __init__(self, results, total):
        self.results = LibgenSearchResults.results
        self.total = total
        
    @staticmethod
    def parse(node, poffset):
    
        SEARCH_ROW_SELECTOR = "/body/table[3]/tr"
        result_rows = xpath(node, SEARCH_ROW_SELECTOR)
        for row in result_rows[1:]:
            book = LibgenBook.parse(row, poffset)
            if book is None:
                continue
            LibgenSearchResults.results.append(book)

        total = len(LibgenSearchResults.results)
        return LibgenSearchResults(LibgenSearchResults.results, total)
        
    @staticmethod
    def clear():
        LibgenSearchResults.results.clear()
        return 0


class LibgenNonFictionClient:
    def __init__(self, mirror=None):
        MIRRORS = [
            "libgen.rs",
            "libgen.is",
            # "libgen.lc",  # Still has the old-style search
            "gen.lib.rus.ec",
            "93.174.95.27",
        ]

        if mirror is None:
            self.base_url = "http://{}/".format(MIRRORS[0])
        else:
            self.base_url = "http://{}/".format(mirror)
        
        self.download_links = {}
        self.update_download_links = []

    def get_page_offset(self, query):
        data = [ 0 ]
        data[-1] = 0 
        data = [ int(s) for s in query.split('p') if s.isdigit() ]
        if data: 
            return data[-1]
        return 0
        
    def search(self, query, max_results):
        self.update_download_links.clear()
        squery = query.decode("utf-8")
        
        poffset = self.get_page_offset(squery)

        vquery = squery.rsplit(' ', 1)[0]
        
        RESULTS_PER_PAGE = 25.0        
        total_pages = int(math.ceil(max_results/RESULTS_PER_PAGE))
        
        url = self.base_url
        
        last_page = poffset + total_pages 

        total_results = 0
        self.total_results = total_results  
        LibgenSearchResults.clear()
        
        urls = []
        for page in range(poffset + 1, last_page + 1):
            query_params = {
                'res': int(RESULTS_PER_PAGE),
                'open': 2,
                'req': vquery,
                'phrase': 1,
                'view' : 'simple',
                'column' : 'def',
                'sort' : 'def',
                'sortmode' : 'ASC',
                'page': page,
            }
            query_string = urlencode(query_params)
            search_url = url + 'search.php?' + query_string
            self.search_url = search_url
            urls.append(search_url)
            self.update_download_links.append(1)
            
        results = ThreadPool(2).imap_unordered(fetch_url, urls)
        parser = etree.HTMLParser()
        
        for cur_url, html, error in results:
            if error is None:
                tree = etree.fromstring(html, parser)       
                result = LibgenSearchResults.parse(tree, poffset)
                total_results = result.total
            else:
                print("error fetching %r: %s" % (cur_url, error))

        self.total_results = total_results
        
        urls.clear()
        
        
        return result

    def get_detail_url(self, md5):
        
        detail_url = '{}book/index.php?md5={}'.format(self.base_url, md5)

        return detail_url
        
    def update_download_urls(self, page):
        self.download_links.clear()
        urls = []

        for i in range(page*25, min( page*25 + 25, len(LibgenSearchResults.results))): 
            book = LibgenSearchResults.results[i]
            urls.append(book.md5)
       
        results = ThreadPool(2).imap_unordered(scrap_download_link, urls)
        parser = etree.HTMLParser()
        
        for cur_url, html, error, md5 in results:
            if error is None and html:
                tree = etree.fromstring(html, parser)
                #SELECTOR = "/body/h2/a[contains(., 'GET')]/@href"
                SELECTOR = "//a[contains(., 'GET')]"
                link = tree.xpath(SELECTOR)          
                final_url = link[0].get('href')       
                self.download_links[md5] = final_url 
                
            else:
                print("error fetching %r: %s" % (cur_url, error))                
        urls.clear()
        return 0
        
    def get_book_page(self, md5):
        RESULTS_PER_PAGE = 25.0
        for i in range(0, len(LibgenSearchResults.results)): 
            book = LibgenSearchResults.results[i]
            if book.md5 == md5:
                return int(math.floor(i/RESULTS_PER_PAGE))
        return 0
        
    def get_download_url(self, md5):
        page = self.get_book_page(md5)
        
        if self.update_download_links[page] == 1:
            self.update_download_links[page] = 2
            self.update_download_urls(page)
            self.update_download_links[page] = 0
            
        while self.update_download_links[page] == 2:
            sleep( randint(50,200)/1000.0)
            
        return self.download_links[md5]
        

if __name__ == "__main__":
    client = LibgenNonFictionClient()
    search_results = client.search("chemical accelerators")

    for result in search_results.results[:5]:
        print(result.title)
        print("Detail", client.get_detail_url(result.md5))
        print("Download", client.get_download_url(result.md5))
