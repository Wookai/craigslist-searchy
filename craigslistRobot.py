from waveapi import events
from waveapi import model
from waveapi import robot
from waveapi import document

import logging
import re
import craigslistStorage
import craigslistParser

craigslistLinkPattern = re.compile('http://[\w\.]+\.craigslist\.(org|ca)/[\w/?=&+%]+')

def OnRobotAdded(properties, context):
  root_wavelet = context.GetRootWavelet()
  waveID = root_wavelet.GetId()
  
  logging.debug('Bot added to wave #%s' % waveID)

  root_wavelet.CreateBlip().GetDocument().SetText("""Thanks for adding me !

To use me, simply add a URL to a result list on Craigslist in your first message.

Please note that it may take a few seconds before the first results are added to the wave.

Because of limitations/bugs of the Wave API, HTML content is not properly displayed, and new results are not automatically added to the wave. Theses features are ready on my side and should (hopefully) be implemented soon.""")


def OnBlipSubmitted(properties, context):
  rootWavelet = context.GetRootWavelet()
  waveID = rootWavelet.GetWaveId()
  waveletID = rootWavelet.GetId()

  # we try to see if a craigslist url is already associated with this wave
  wave = craigslistStorage.GetWave(waveID)

  # if not, we look for that URL in the root blip
  if wave is None:
    logging.debug('No url associated with wave #%s' % waveID)
    
    rootBlipId = rootWavelet.GetRootBlipId()
    rootBlip = context.GetBlipById(rootBlipId)
    doc = rootBlip.GetDocument()
    
    url = craigslistLinkPattern.search(doc.GetText())

    # if the url is found, store it
    if url is not None:
      searchUrl = url.group(0)
      logging.debug('URL found : %s' % searchUrl)

      wave = craigslistStorage.AddWave(waveID, waveletID, searchUrl)
      rootWavelet.CreateBlip().GetDocument().SetText('I found an URL ! I will now monitor %s and add search results to this wave !' % searchUrl)
    else:
      logging.debug('URL not found in root blip. Aborting...')
      return

    # now that we have the URL, let's fetch the result
    CraigslistWaveUpdater(context, wave)

class CraigslistWaveUpdater:
  def __init__(self, context, wave):
    """ Initiates a robot that will update the search results of the given craigslist wave """
    self.wave = wave
    self.googleWave = context.GetWaveById(wave.waveID)
    self.wavelet = context.GetWaveletById(wave.waveletID)
    self.UpdateResults()

  def UpdateResults(self):
    """ Parses the search results webpage to look for new items """
    logging.debug('Updating results for wave %s' % self.wave.waveID)
    
    # let's get the results we already have for this wave
    knownItems = craigslistStorage.GetWaveItemUrls(self.wave)

    # now, parse search results and look for new ones
    craigslistParser.ResultsList(self.wave.searchUrl, knownItems, self.NewResultItemFound)

  def NewResultItemFound(self, item):
    """ This method is called by the parser each time a new item was found """
    logging.debug('Adding new item %s to wave %s' % (item.url, self.wave.waveID))

    # add the item to the list of items of the wave
    craigslistStorage.AddResultItem(self.wave, item.url)

    # create a new blip with the item details
    doc = self.wavelet.CreateBlip().GetDocument()

    doc.AppendText('%s\n\n' % item.url)
    doc.AppendText('%s (%s)\n\n' % (item.title, item.location))
    doc.AppendText('Date: %s\nReply to: %s\n\n' % (item.date, item.email))
    doc.AppendText(item.text + '\n')

    for url in item.imageURLs:
      doc.AppendText('\n')
      doc.AppendElement(document.Image(url=url))


if __name__ == '__main__':
  myRobot = robot.Robot('Craigslist Searchy',
      image_url='http://craigslist-searchy.appspot.com/assets/images/logo.png',
      version='1.1.7',
      profile_url='http://craigslist-searchy.appspot.com/')
  myRobot.RegisterHandler(events.BLIP_SUBMITTED, OnBlipSubmitted)
  myRobot.RegisterHandler(events.WAVELET_SELF_ADDED, OnRobotAdded)
#  myRobot.RegisterCronJob('/update', 60)
  myRobot.Run()
