from google.appengine.api import memcache

import urllib
import re
import urlparse
import logging
import dateutil.parser


class ResultItem:
    """ A result item contains the data corresponding to one ad on craigslist. """
    
    def __init__(self, match, baseUrl):
        """ Initializes the item with the data matched on the results list page """
        self.title = match.group('title')
        self.path = match.group('path')
        
        # prevent encoding errors
        self.title = unicode(self.title, "utf-8", errors="replace")

        # set full URL of item
        if self.path.find('http://') > -1:
            # results from NEARBY areas already have absolute URLs
            self.url = self.path
        else:
            # local results have relative URLs
            self.url = 'http://' + baseUrl + self.path
            
        self.location = match.group('location')
        self.text, self.date, self.email = '', '', ''
        self.imageURLs = []
        
    def __str__(self):
        """ ToString() method for debugging """
        value = 'Title:\t%s\n' % self.title
        value += 'City:\t%s\n' % self.location
        value += 'Path:\t%s\n' % self.path
        value += 'URL:\t%s\n' % self.url
        value += 'Date:\t%s\n' % self.date
        value += 'Email:\t%s\n' % self.email

        for url in self.imageURLs:
            value += 'Image:\t%s\n' % url

        value += 'Text:\t%s' % self.text
        
        return value


class ResultsList:
    """ Reprensents a list of results as found when performing a search on craigslist.

        The result items are first parsed from the results list, and then their details
        are fetched from their own page.
    """
    resultItemPattern = re.compile('<p>[^<]*<a href="(?P<path>[^"]+)">(?P<title>[^<]+) -</a>(<font[^>]+> \((?P<location>[^<]+)\)</font>)?(\s*<span[^>]+>[^<]+</span>)*')
    detailsTextPattern = re.compile('<div id="userbody">\s+(?P<content>.+)\s*(<!-- START CLTAGS -->|<br><br>(.+)?<ul>\s+<li>)', re.DOTALL)
    detailsImagePattern = re.compile('<td align="center"><img src="(?P<url>[^"]+)" alt="image \d+-\d"></td>')
    detailsDateEmailPattern = re.compile('<hr>\s+Date: (?P<date>[^<]+)<br>\s+Reply to: ((<a[^>]+>)?(?P<email>[^<]+)(</a>)?)')

    def __init__(self, url, knownItems, ItemFoundCallback):
        """ Initializes a list of results for the given url.

            knownItems contains the list of items that were already seen for this search.
            Each time a new item is found, the callback method is called with this item to process it.

            Details for each item are either fetched from the cache, or parsed from their own page.
        """
        parsedUrl = urlparse.urlparse(url)
        
        self.url = url
        self.baseUrl = parsedUrl.netloc
        
        html = urllib.urlopen(url).read()
        matches = []

        for match in self.resultItemPattern.finditer(html):
            matches.append(match)

        # reverse matches, such that the older items are added first
        matches.reverse()

        # parse items and get details
        for match in matches:
            item = ResultItem(match, self.baseUrl)
            print item.url

            # do not consider items that we have already seen
            if item.url in knownItems:
                continue

            # try to get it from the cache first
            cachedItem = memcache.get(item.url)

            if cachedItem is not None:
                logging.debug('Item found in the cache : %s' % item.url)
                item = cachedItem
            else:
                logging.debug('Fetching item details from url : %s' % item.url)
                if self.getItemDetails(item):
                    memcache.set(item.url, item)
                else:
                    logging.debug('Unable to get details, item ignored')
                    item = None

            # notify if a new item was found
            if item is not None:
                ItemFoundCallback(item)

    def getItemDetails(self, item):
        """ Get the text and images of an item by parsing its webpage. """
        html = urllib.urlopen(item.url).read()
        item.text = self.detailsTextPattern.search(html)

        # posting removed ?
        if item.text is None:
            return False
        else:
            item.text = item.text.group('content')

        # prevent encoding errors
        item.text = unicode(item.text, "utf-8", errors="replace")

        for i in self.detailsImagePattern.finditer(html):
            item.imageURLs.append(i.group('url'))

        dateEmail = self.detailsDateEmailPattern.search(html)
        item.date = dateEmail.group('date') # dateutil.parser.parse(dateEmail.group('date'))
        item.email = dateEmail.group('email')

        return True
