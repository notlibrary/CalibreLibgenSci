# CalibreLibgenSci
A Libgen Non-Fiction/Sci-tech store plugin for [Calibre](https://calibre-ebook.com)

## Installation
- Download the latest zip file release from [here](https://github.com/notlibrary/CalibreLibgenSci/releases)
- Open Calibre
- Navigate to Preferences -> Plugins (in the advanced section) -> Load Plugin from File and select the zip file you downloaded.
- Restart Calibre

## Usage
- Click the 'Get Books' menu in Calibre
- Ensure that 'Libgen Sci-tech' is selected in the search providers menu

    ![image](https://user-images.githubusercontent.com/40695473/149553512-ce27e902-96bc-48d2-a0db-1564aa87e44c.png)
- Search!
- For Fiction books library [install other plugin](https://github.com/fallaciousreasoning/CalibreLibgenStore/releases)

## Testing & development

While working on any of the scripts, run this to update the plugin in Calibre and start it in debug mode:

```shell
 calibre-debug -s; calibre-customize -b .; calibre-debug -g
```

## Build a release

Run this to zip all required files together:

```shell
make
```
## P.S.
I wouldn't maintain it anymore just forked it from fiction parser for fun and profit.  