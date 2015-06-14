import sys
import time
import math
import argparse
import logging
import tldextract
from Queue import Queue, Empty as QueueEmpty
from crawl_url import Fetcher, Parser

USAGE = "python crawl.py -u <url> -d [depth] -v [maximum vebosity]"
DESCRIPTION = "A simple webcrawler using a non blocking queue repository [ctrl + c to exit]"
LINK_FILE = "url_links.txt"
 
class Crawler(object):
    """ Master crawler class with queue as the repository of links"""
    def __init__(self, root, depth, logger=None, domain_only = False):
        self.logger = logger or logging.getLogger(__name__)
        self.root = root
        self.depth = depth
        self.link_q = Queue()
        self.followed = -1
        self.followed_links = []
        self.urls = []
        self.domain_only = domain_only
        if domain_only:
           no_fetch_extract = tldextract.TLDExtract(fetch=False)
           self.domain_only = no_fetch_extract(self.root).domain

    def __fetch_url(self, url):
	""" Fetching and parsing links for each page"""
        root = Fetcher(self.root, logger=self.logger)
        root.fetch()
        if not root.content:
            return []

        self.logger.debug("Parsing content .. ")
        page = Parser(url, root.content, domain_only = self.domain_only)
        page.content_parser()
        return page.url_list

    def __link_validator(self, urls, url):
        lnk_arr = []
        for lnk in set(urls):
            lnk = lnk.strip("/")
            ### To exclude links like "https://www.facebook.com/#, https://www.python.org/#content"
            if "#" in lnk and ( lnk.split('#')[0].strip("/") in self.followed_links or \
                                lnk.split('#')[0].strip("/") == url):
               continue            

            if lnk not in self.urls and lnk not in self.followed_links:
               lnk_arr.append(lnk)
        return lnk_arr
        
    def standard_crawl(self):
	""" Standard Crawling starts from here, Queue is made the link repository
            Queue is non blocking so as to exit while queu is empty
	"""
        url = self.root
        self.link_q.put(url)
        self.followed_links = [url]
        self.logger.debug("CRAW..L..ING.. .. %s" % str(url))
        while True:
            try:
                url = self.link_q.get(False)
            except QueueEmpty:
                break
            try:
                self.logger.info("Crawling %s Link: %d" % (str(url), (self.followed+1)))
                urls = self.__fetch_url(url)
                self.followed_links.append(url.strip("/"))
                self.logger.debug(" %d Links found" % int(len(urls)))
                lnk_arr = self.__link_validator(urls, url)
                for lnk in lnk_arr:
                    self.link_q.put(lnk)
                self.logger.info(" %d Links added" % int(len(lnk_arr)))
                self.urls.extend(lnk_arr)
                self.logger.debug("Finished  Crawling %s " % str(url))
                self.followed += 1

                if self.followed >= self.depth and self.depth > 0:
                    self.logger.debug("Specified depth reached")
                    break
            except KeyboardInterrupt:
                self.logger.error("Keyboard Interrupt pressed .. exiting ..  ")
                break
            except UnicodeError, err:
                self.logger.error("ERROR: Can't process url content unicode error '%s' (%s)" % (url, err))
            except Exception, err:
                self.logger.error("ERROR: Can't process url '%s' (%s)" % (url, err))

def write_links_to_file(filename, links):
    """Write all the links found to a file """
    try:
        with open(filename, "wb") as filehandle:
            for link in links:
                filehandle.write(str(link)+"\n")
        return True
    except IOError:
        return False


def parse_options():
    """parse_options() -> opts, parser

    Parse any command-line options given returning both
    the parsed options and arguments.
    """

    parser = argparse.ArgumentParser(usage = USAGE, description = DESCRIPTION)

    parser.add_argument("-u", "--url", dest="url", help="Root url to crawl")
    parser.add_argument("-o", "--output", dest="output",help="if specified \
                           writes it to the file [default : url_links.txt]")
    parser.add_argument("-v", "--verbose",
            action="store_true", default=False, dest="verbose",
            help="Enable maximum verbosity")
    parser.add_argument("-d", "--depth",
            action="store", type=int, default=-1, dest="depth",
            help="Maximum depth to traverse")
    parser.add_argument("-r", "--restricted",
            action="store_true", default=False, dest="domain_only",
            help="Restrict links to root domain")
    return  parser.parse_args(), parser

def get_logger(level, filename="crawl.log"):
    format_log = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename=filename, level=level, format=format_log)
    logger = logging.getLogger("crawler")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(format_log))
    logger.addHandler(handler)
    return logger

def main():
    """Start point for the command line program"""
    opts, parser = parse_options()
    if  not opts.url:
        parser.print_help()
	sys.exit()
    level = logging.INFO
    output = LINK_FILE
    if opts.verbose: 
        level = logging.DEBUG
    if opts.output:
       output = opts.output
    logger = get_logger(level)
    s_time = time.time()
    logger.info("#"*50)
    logger.info("Crawling %s (Max Depth: %d)" % (opts.url, opts.depth))
    logger.info("#"*50)
    crawler = Crawler(opts.url, opts.depth, logger=logger,domain_only = opts.domain_only)
    crawler.standard_crawl()

    e_time = time.time()
    t_time = e_time - s_time

    logger.info("Found:    %d" % len(crawler.urls))
    logger.info("Followed: %d" % crawler.followed)
    logger.info("Stats:    (%d/s after %0.2fs)" % (int(math.ceil(float(len(crawler.urls)) / t_time)), t_time))
    if write_links_to_file(output, crawler.urls):
       logger.info("Link file:: %s" % output)
    else:
       logger.info("Unable to write links to file:: %s" % output)
if __name__ == "__main__":
     main()
