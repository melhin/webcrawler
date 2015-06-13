import sys
import time
import math
import argparse
import logging
from Queue import Queue, Empty as QueueEmpty
from crawl_url import Fetcher, Parser

USAGE = "python crawl.py -u <url> -d [depth] -v [maximum vebosity]"
DESCRIPTION = "A simple webcrawler using a non blocking queue repository [ctrl + c to exit]"
LINK_FILE = "url_links.txt"
 
class Crawler(object):
    """ Master crawler class with queue as the repository of links"""
    def __init__(self, root, depth, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.root = root
        self.depth = depth
        self.link_q = Queue()
        self.followed = -1
        self.urls = []

    def __fetch_url(self, url):
	""" Fetching and parsing links for each page"""
        root = Fetcher(self.root, logger=self.logger)
        root.fetch()
        if not root.content:
            return []

        self.logger.debug("Parsing content .. ")
        page = Parser(url, root.content)
        page.content_parser()
        return page.url_list

        
    def standard_crawl(self):
	""" Standard Crawling starts from here, Queue is made the link repository
            Queue is non blocking so as to exit while queu is empty
	"""
        url = self.root
        self.link_q.put(url)
        followed = [url]

        self.logger.debug("CRAW L ING.. .. %s" % str(url))
        while True:
            try:
                url = self.link_q.get(False)
            except QueueEmpty:
                break
            ### To exclude links like "https://www.facebook.com/#, https://www.python.org/#"
            if "#" in url and url.split('#')[0] in followed and \
        	len(url.split("#")[1].split("/")) < 2: continue            
            try:
                self.logger.info("Crawling %s Link: %d" % (str(url), (self.followed+1)))
                urls = self.__fetch_url(url)
                followed.append(url)
                new_ent = set(urls) - set(self.urls)
                self.urls.extend(new_ent)
                for lnk in new_ent:
                    self.link_q.put(lnk)
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
        with open(filename, "wb") as fh:
            for link in links:
                fh.write(str(link)+"\n")
        return True
    except IOError:
        logger.error("Write to file failed .. ")
        return False


def parse_options():
    """parse_options() -> opts, parser

    Parse any command-line options given returning both
    the parsed options and arguments.
    """

    parser = argparse.ArgumentParser(usage = USAGE, description = DESCRIPTION)

    parser.add_argument("-u", "--url", dest="url", help="Root url to crawl")
    parser.add_argument("-v", "--verbose",
            action="store_true", default=False, dest="verbose",
            help="Enable maximum verbosity")

    parser.add_argument("-d", "--depth",
            action="store", type=int, default=-1, dest="depth",
            help="Maximum depth to traverse")
    return  parser.parse_args(), parser

def main():
    """Start point for the command line program"""
    opts, parser = parse_options()
    if  not opts.url:
        parser.print_help()
	sys.exit()
    level = logging.INFO
    if opts.verbose: 
        level = logging.DEBUG
    
    logging.basicConfig(filename='crawl.log', level=level)
    logger = logging.getLogger("crawler")
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    s_time = time.time()

    logger.info("Crawling %s (Max Depth: %d)" % (opts.url, opts.depth))
    crawler = Crawler(opts.url, opts.depth, logger=logger)
    crawler.standard_crawl()

    e_time = time.time()
    t_time = e_time - s_time

    logger.info("Found:    %d" % len(crawler.urls))
    logger.info("Followed: %d" % crawler.followed)
    logger.info("Stats:    (%d/s after %0.2fs)" % (int(math.ceil(float(len(crawler.urls)) / t_time)), t_time))
    if write_links_to_file(LINK_FILE, crawler.urls):
       logger.info("Link file:: %s" % LINK_FILE)
if __name__ == "__main__":
     main()
