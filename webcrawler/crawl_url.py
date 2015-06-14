import logging
import urllib2 
import urlparse
import re
import tldextract
from cgi import escape
from bs4 import BeautifulSoup

class Parser(object):
    """Parse links from the content of the page"""
    def __init__(self, url, content, domain_only = False): 
        self.url = url
        self.content = content
        self.url_list = []
        ### Regex for valid url check
        self.regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
	self.domain_only = domain_only
        if self.domain_only:
            self.no_fetch_extract = tldextract.TLDExtract(fetch=False)
 
    def __domain_check(self, url, domain_only):
        """ Advanced check for extracting links related to domain"""
        if not domain_only:
            return True
        url_det = self.no_fetch_extract(url)
        if url_det.domain == domain_only:
           return True
	return False

    def __tag_parser(self, tags):
        """Populate the url list with urls from the site"""
        for tag in tags:
            href = tag.get("href")
            if href:
                url = urlparse.urljoin(self.url, escape(href))
		###Check if url is valid
                if url is not None and self.regex.search(url) and \
                          self.__domain_check(url, self.domain_only):
		    self.url_list.append(url)

    def content_parser(self):
        """ Parse content and get the linke """
        soup = BeautifulSoup(self.content)
        tags = soup('a')
        self.__tag_parser(tags)
	

class Fetcher(object):
    """ Links will be passed on and then opened from here"""
    def __init__(self, url, url_timeout=30, agent = "Mozilla", logger=None):
	self.logger = logger or logging.getLogger(__name__)
        self.url = url
        self.url_timeout = url_timeout
        self.agent = agent
        self.content = None

    def __add_headers(self, request):
        """Place holder for adding random agents"""
        request.add_header("User-Agent", self.agent)

    def open(self):
        """Build opener from here"""
	response = None
        try:
            request = urllib2.Request(self.url)
            self.__add_headers(request)
            response = urllib2.urlopen(request, timeout = self.url_timeout)
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
