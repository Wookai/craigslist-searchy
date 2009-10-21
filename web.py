from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

from waveapi import robot_abstract

import os
import urllib
import re
import craigslistParser
import craigslistStorage
import logging
import sys

class MainPage(webapp.RequestHandler):
  count = 0
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    print ''

    waveId = 'asdfasdfa'
    waveletId = '1234jl1234'
    url = 'http://cnj.craigslist.org/search/apa?query=&catAbbreviation=apa&minAsk=min&maxAsk=500&bedrooms=2&hasPic=1'

    self.wave = craigslistStorage.AddWave(waveId, waveletId, url)
    knownItems = []# craigslistStorage.GetWaveItemUrls(self.wave)
    
    print ''
    print 'Wave known items : ', knownItems
    
    craigslistParser.ResultsList(url, knownItems, self.PrintItem)
    print 'New items found:', self.count
  
  def PrintItem(self, item):
      craigslistStorage.AddResultItem(self.wave, item.url)
      self.count += 1

class GadgetPage(webapp.RequestHandler):
  def get(self):
    movieID = self.request.get('movieID')

    self.response.headers['Content-Type'] = 'text/xml'
    path = os.path.join(os.path.dirname(__file__), 'gadget.html')
    self.response.out.write(template.render(path, template_values))


class UpdateWavesPage(webapp.RequestHandler):
  def get(self):
    logging.debug('Update get called !')
    logging.debug(self.request)
    
    self.response.headers['Content-Type'] = 'text/plain'

    waves = craigslistStorage.GetAllWaves()

    print ''
    print 'Updating waves...'
    
    for w in waves:
      print '\t', w.waveID, '\t', w.searchUrl

  def post(self):
    logging.debug('Update post called !')
    json_body = sys.stdin.read() 
    logging.debug(json_body)
    context, events = robot_abstract.ParseJSONBody(json_body)
    logging.debug(context)
    logging.debug(events)
    

class FlushCachePage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'

    if memcache.flush_all():
      self.response.out.write('Memcache flushed')
    else:
      self.response.out.write('Cannot flush cache !')

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/gadget.xml', GadgetPage),
                                      ('/flush', FlushCachePage),
                                      ('/update', UpdateWavesPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
