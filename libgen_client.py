#!/usr/bin/env python3

from lxml import etree
import random
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import parse_qs

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
    def __init__(self, libid, authors, title, series, publisher, year , pages, language, file_size, file_extension, mirrors, md5, image_url):
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

    @staticmethod
    def parse(node):
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
        authors = ' & '.join([
            author.text for author in xpath(node, AUTHOR_XPATH)
        ])

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

        if not authors or not title:
            return None

        return LibgenBook(libid, authors, title, series, publisher, year , pages, language, file_size, file_extension, mirrors, md5,  None)


class LibgenSearchResults:
    def __init__(self, results, total):
        self.results = results
        self.total = total
        
    @staticmethod
    def parse(node):
    
        SEARCH_ROW_SELECTOR = "/body/table[3]/tr"
        result_rows = xpath(node, SEARCH_ROW_SELECTOR)
        results = []
        for row in result_rows[1:]:
            book = LibgenBook.parse(row)
            if book is None:
                continue
            results.append(book)

        total = len(results)
        return LibgenSearchResults(results, total)


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

    def search(self, query, max_results, total_pages):
        url = self.base_url
        query_params = {
            'req': query,
            'open': 2,
            'res': max_results,
            'page': 1,
        }

        query_string = urlencode(query_params)
        search_url = url + 'search.php?' + query_string
        self.search_url = search_url
        
        request = urlopen(search_url)
        html = request.read()

        parser = etree.HTMLParser()
        tree = etree.fromstring(html, parser)
        
        result = LibgenSearchResults.parse(tree)
        
        self.total_results = result.total
        return result

    def get_detail_url(self, md5):
        detail_url = '{}book/index.php?md5={}'.format(self.base_url, md5)

        return detail_url

    def get_download_url(self, md5):
        download_urls = [
            'http://library.lol/main/{}'.format(md5),
            'http://library.lol/main/{}&open=2'.format(md5),
            'http://library.lol/main/{}&open=1'.format(md5),
            'https://3lib.net/md5/{}&open=2'.format(md5),
            'http://bookfi.net/md5/{}&open=2'.format(md5),
        ]

        for url in download_urls:
            try:
                request = urlopen(url)
                html = request.read()

                parser = etree.HTMLParser()
                tree = etree.fromstring(html, parser)

                #SELECTOR = "/body/h2/a[contains(., 'GET')]/@href"
                SELECTOR = "//a[contains(., 'GET')]"
                link = tree.xpath(SELECTOR)
                
                
                final_url = link[0].get('href')
                return final_url
            except:
                continue

if __name__ == "__main__":
    client = LibgenNonFictionClient()
    search_results = client.search("chemical accelerators")

    for result in search_results.results[:5]:
        print(result.title)
        print("Detail", client.get_detail_url(result.md5))
        print("Download", client.get_download_url(result.md5))
