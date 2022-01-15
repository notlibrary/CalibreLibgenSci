version = 0.4.2

zip_file = releases/Libgen Non-Fiction v$(version).zip
zip_contents = *.py LICENSE *.md *.txt

all: zip

zip:
	@ echo "creating new $(zip_file)" && zip "$(zip_file)" $(zip_contents) && echo "created new $(zip_file)"

install: zip
	@ echo "installing plugin from file"
	calibre-debug -s
	calibre-customize -a "$(zip_file)"
	
clean:
	rm $(zip_file)