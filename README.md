# WebCrawler
============

A simple webcrawler using a non blocking queue repository 
with support for extracting links only from root domain

***Usage***

 python crawl.py -u <url> [ -d <depth> -v  -r -o <filename> ] 

 [ctrl + c to interuppt crawling]

***Arguments***
-  -h, --help            show this help message and exit
-  -u, --url             Root url to crawl
-  -o, --output          If specified writes it to the file [default : url_links.txt]
-  -v, --verbose         Enable maximum verbosity
-  -d, --depth           Maximum depth to traverse
-  -r, --restricted      Restrict links to root domain
