<h1 align="center">
  <img src="/static/logo.webp" alt="spyder" width="400px">
  <br>
</h1>

<h3 align="center">
it's not finished yet, but all the features listed are available.
</h3>

## Features

- **Fast Crawling**
- **Recrawling**
- **Dir Search**
- **Recursive Search**
- **404 Page Detection**
- **Custom Exporter**

## Installation
```
git clone --depth 1 https://github.com/GuiDotPy/spyder.git
```
>it still doesn't install mongodb automatically, so you need to install and run it.

## Usage
```
cat urls.txt | python spyder.py scan -crawler
```

## Flags

```console
POSITIONAL ARGUMENTS:
  scan
  exporter

SCAN:
  -h, --help             show this help message and exit
  -dir                   use dir search
  -crawler               use only crawler
  -c, --max-concurrency  maximum concurrent requests
  -mt, --max-timeout     maximum number of retests that can be taken when there is a timeout
  -mrc, --max-recrawl    maximum recrawl
  -ss, --skip-status     skip responses with this status
  -st, --skip-text       skip responses with this text in body
  -su, --skip-urls       skip responses with this text in url
  -H, --headers          set custom headers
  -r, --scope-regex      use a regex to set additional in-scope domains
  -p, --use_proxy        use proxy
  -k, --keep-previous    keep previous scan
  --no-required-404      only check urls that have a status/message 404 [default: True]
  
EXPORTER:
  -h, --help                   show this help message and exit
  -es, --export-status         export url by status
  -ect, --export-content-type  export url by content-type
  -er, --export-regex          export urls that match the specified regex
  -eurls, --export-urls        export all urls
  -ed, --export-downloadable   export downloadable urls
```

## Tips & Recommendations
- by default, it uses all domains of urls from stdin as in-scope. you can use the `-r` to set a regex as an additional scope.
- you don't need to use the `-dir` and `-crawler` together, `-dir` already crawl all urls found.
