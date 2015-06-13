import logging
import urllib2 
import urlparse
import re
from cgi import escape
from bs4 import BeautifulSoup

AGENT = "Mozilla"
URL_TIMEOUT = 30

class Parser(object):
    """Parse links from the content of the page"""
    def __init__(self, url, content):
        self.url = url
        self.content = content
        self.url_list = []
        self.regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def __tag_parser(self, tags):
        for tag in tags:
            href = tag.get("href")
            if href:
                url = urlparse.urljoin(self.url, escape(href))
                if url is not None and self.regex.search(url):
		    self.url_list.append(url)

    def content_parser(self):
        soup = BeautifulSoup(self.content)
        tags = soup('a')
        self.__tag_parser(tags)
	

class Fetcher(object):
    """ Links will be passed on and then opened from here"""
    def __init__(self, url, logger=None):
	self.logger = logger or logging.getLogger(__name__)
        self.url = url
        self.content = None

    def __add_headers(self, request):
        request.add_header("User-Agent", AGENT)

    def open(self):
        """Build opener from here"""
	response = None
        try:
            request = urllib2.Request(self.url)
            self.__add_headers(request)
            response = urllib2.urlopen(request, timeout=URL_TIMEOUT)
        except urllib2.HTTPError, error:
            if error.code == 404:
                 self.logger.error("ERROR: %s -> %s" % (error, error.url))
            else:
                 self.logger.error("ERROR: %s" % error)
        except urllib2.URLError, error:
             self.logger.error("ERROR: %s not valid " % self.url)
        return response

    def fetch(self):
        """ Request content"""
        response = self.open()
        if not response:
             self.logger.error(str(self.url)+" response invalid")
             return None

        self.logger.debug("Sending request .. ")
        self.content = unicode(response.read(), "utf-8",\
               errors="replace",)

        self.logger.debug("Response Received .. ")
