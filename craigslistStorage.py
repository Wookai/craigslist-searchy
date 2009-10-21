from google.appengine.ext import db

import logging


class CraigslistWave(db.Model):
    """ Represents a wave that monitors a craigslist search """
    waveID = db.StringProperty()
    waveletID = db.StringProperty()
    searchUrl = db.StringProperty()

class ResultItem(db.Model):
    """ Reprensents a search result item seen by a given wave """
    url = db.StringProperty()
    wave = db.ReferenceProperty(CraigslistWave)


def AddWave(waveID, waveletID, searchUrl):
    """ Adds a wave to monitor the given search Url """
    wave = GetWave(waveID)

    if wave is None:
        logging.debug('Adding monitoring of wave %s for %s' % (waveID, searchUrl))
        wave = CraigslistWave(waveID=waveID, waveletID=waveletID, searchUrl=searchUrl)
        wave.put()
        
    return wave

def GetWave(waveID):
    """ Gets the craigslist wave with the given waveID """
    query = CraigslistWave.gql('WHERE waveID = :1', waveID)
    results = query.fetch(1)

    if len(results) == 1:
        return results[0]
    else:
        return None

def GetAllWaves():
    return CraigslistWave.all()

def GetWaveItems(wave):
    """ Gets all search result items related to the given craigslist wave """
    return ResultItem.gql('WHERE wave = :1', wave.key())

def GetWaveItemUrls(wave):
    """ Gets the list of search results URLs already seen by the given wave """
    items = GetWaveItems(wave)
    return [item.url for item in items]

def AddResultItem(wave, itemUrl):
    """ Adds a search result URL to the given craigslist wave"""
    item = ResultItem(url=itemUrl, wave=wave)
    item.put()
    return item
