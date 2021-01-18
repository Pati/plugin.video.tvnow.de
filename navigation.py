#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import requests
try:
    import urllib.parse as ul
except:
    import urllib as ul
import json
import datetime
import time
import re
import resources.lib.common as common
from sendung import Sendung
import tvnow
apiBase = "https://bff.apigw.tvnow.de"
formatImageURL = "https://ais.tvnow.de/tvnow/format/{fid}_formatlogo/408x229/image.jpg"
episodeImageURL = "https://ais.tvnow.de/tvnow/movie/{eid}/408x229/image.jpg"
addon_handle = int(sys.argv[1])
try:
    #py2
    icon_file = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
except:
    icon_file = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png')
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
addon = xbmcaddon.Addon()
plotEnabled = addon.getSetting('plot_enabled') == "true"


def parseDateTime(str):
    try:
        m = re.search(r'[A-z]+\.\s+([0-9]+).([0-9]+).([0-9]+),\s+([0-9]+):([0-9]+)', str)
        if m:
            return datetime.datetime(int(m.group(3)),int(m.group(2)), int(m.group(1)), int(m.group(4)), int(m.group(5)))
    except:
        return None

def buildDirectoryName(data):
    dirName = ""
    episode = data["items"][0]
    if "ecommerce" in episode:
        ecommerce = episode["ecommerce"]
        if "teaserFormatName" in ecommerce:
            dirName = ecommerce["teaserFormatName"]
    if "ecommerce" in data and "rowName" in data["ecommerce"]:
        dirName = "%s - %s" % (dirName, data["ecommerce"]["rowName"])
    return dirName

def getEpName(episode, info):
    epNameSuffix = ""
    epNamePrefix = ""
    epName = ""
    if "ecommerce" in episode:
        ecommerce = episode["ecommerce"]
        if "teaserEpisodeAirtime" in ecommerce:
            dt = parseDateTime(ecommerce["teaserEpisodeAirtime"])
            epNameSuffix = ecommerce["teaserEpisodeAirtime"]
            if dt:
                info["date"] = dt.strftime('%Y-%m-%d')
                info["premiered"] = dt.strftime('%Y-%m-%d')
                info["aired"] = dt.strftime('%Y-%m-%d')
                info["dateadded"] = str(dt)
        if "teaserEpisodeNumber" in ecommerce:
            epNamePrefix =  ecommerce["teaserEpisodeNumber"]
        if "teaserEpisodeName" in ecommerce:
            epName = ecommerce["teaserEpisodeName"]
        elif "teaserName" in ecommerce:
            epName = ecommerce["teaserName"]
    epString = ""
    if epNamePrefix != "":
        epString = "%s: " % epNamePrefix 
    if epName != "":
        epString = "%s%s" % (epString, epName)
    else:
        epName = "%s%s" % (epString, episode['headline'])
    if epNameSuffix != "":
        epString = "%s (%s)" % (epString, epNameSuffix)
    return epString, info

class Navigation():
    def __init__(self,db):
        self.db = db
        self.showPremium = (addon.getSetting('premium') == "true")
        self.showlive = (addon.getSetting('liveFree') == "true")
        self.showLivePay = (addon.getSetting('livePay') == "true")
    
    def getInfoLabel(self, data, movie=False):
        info = {}
        info['title'] = data.get('headline', '')
        if not data.get('year_of_production', '') == '':
            info['year'] = data.get('year_of_production', '')
        if movie:
            if "description" in data:
                info['plot'] = data.get('description', '').replace('\n', '').strip()
            elif "seo" in data:
                info['plot'] = data["seo"].get('text', '').replace('\n', '').strip()
                info['plot'] = re.sub('<[^<]+?>', '', info['plot'])
        else:
            info['plot'] = data.get('text', '').replace('\n', '').strip()
        return info
    
    def login(self):  
        keyboard = xbmc.Keyboard('', 'E-Mail-Adresse')
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            username = keyboard.getText()
            password = self.setLoginPW()
            if password != '': 
                TvNow = tvnow.TvNow()
                if TvNow.sendLogin(username, password):
                    xbmcgui.Dialog().notification('Login erfolgreich', 'Angemeldet als "' + username + '".', icon=xbmcgui.NOTIFICATION_INFO)
                    return True
                else:
                    return False
                    
    def search(self):
        keyboard = xbmc.Keyboard('', 'Suchbegriff')
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            query = keyboard.getText()
            if query != '':
                self.listSearchResult(query)
                    
    def setLoginPW(self):
        keyboard = xbmc.Keyboard('', 'Passwort', True)
        keyboard.doModal(60000)
        if keyboard.isConfirmed() and keyboard.getText() and len(keyboard.getText()) >= 6:
            password = keyboard.getText()
            return password
        return ''
        
    def listDictCategories(self, dicttype=""):
        d = self.db.getDict(dicttype)
        for item in sorted(d.keys()):
            url = common.build_url({'action': 'listDict'.encode('utf-8'), 'id': item, 'dict'.encode('utf-8') : dicttype.encode('utf-8')})
            li = xbmcgui.ListItem(item)
            li.setArt({'icon': icon_file})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def listDict(self, dictkey,dicttype=""):
        d = self.db.getDict(dicttype)
        for item in d[dictkey]:
            url = common.build_url({'action': 'listPage'.encode('utf-8'), 'id': item.sid.encode('utf-8')})
            li = xbmcgui.ListItem(item.title)
            sid = item.sid.split("-")[-1]
            imgurl = formatImageURL.replace("{fid}",str(sid))
            li.setArt({'poster': imgurl, 'icon': icon_file})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
        
    def listLiveTV(self):
        tvNow = tvnow.TvNow()
        if tvNow.login():
            url = apiBase + "/module/teaserrow/epglivetv"
            r = requests.get(url)
            data = r.json()
            for item in data["items"]:
                baseJSON = item["station"][0]["now"]
                stationName = baseJSON["station"]
                stationID = baseJSON["id"]
                payTV = item["pay"]

                xbmcplugin.setPluginCategory(addon_handle, "LiveTV")
                xbmcplugin.setContent(addon_handle, 'episodes')
                if self.showlive and (payTV == False or self.showLivePay):
                    url = common.build_url({'action': 'playLive', 'vod_url': stationID})
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    li.setInfo('video', "")
                    li.setLabel('%s' % (stationName))
                    li.setArt({'poster': baseJSON["image"][0]["src"]})
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                listitem=li, isFolder=False)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def rootDir(self):       
        url = common.build_url({'action': 'listDictCats', 'id': 'Az'})
        li = xbmcgui.ListItem()
        li.setLabel('Sendungen A-Z')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                   listitem=li, isFolder=True)
        url = common.build_url({'action': 'listDictCats', 'id': 'station'})
        li = xbmcgui.ListItem()
        li.setLabel('Sendungen nach Sender')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                   listitem=li, isFolder=True)
        url = common.build_url({'action': 'listLive'})
        li = xbmcgui.ListItem()
        li.setLabel('LiveTV')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                   listitem=li, isFolder=True)
                                   
        url = common.build_url({'action': 'search'})
        li = xbmcgui.ListItem()
        li.setLabel('Suche')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                   listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def listEpisodesFromSeasonByYear(self, year, month, serial_url):
        url = apiBase + serial_url + "?year=" + year + '&month=' + month
        r = requests.get(url)
        data = r.json()
        totalItems = len(data['items'])
        if totalItems > 0:
            xbmcplugin.setContent(addon_handle, 'EPISODES')
            xbmcplugin.setPluginCategory(addon_handle,buildDirectoryName(data))
            xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
            for episode in data['items']:
                if self.showPremium or episode["isPremium"] == False:
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    videoId = episode['videoId']
                    fID = serial_url.split('/')[-1]
                    if plotEnabled:
                        url = "{}/{}/{}?episodeId={}".format(apiBase, "module/teaserrow/format/highlight",fID, videoId)
                        r = requests.get(url)
                        data = r.json()
                        epData = data["items"][0]
                    else:
                        epData = episode
                    info = self.getInfoLabel(epData)
                    epName, info = getEpName(episode, info)
                    info['title'] = epName
                    li.setInfo('video',info)
                    li.setLabel('%s' % (epName))
                    li.setArt({'poster': episodeImageURL.replace("{eid}",str(episode['id'])), 'clearlogo': formatImageURL.replace("{fid}",str(fID))})
                    url = common.build_url({'action': 'playVod', 'vod_url': episode["videoId"]})
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                listitem=li, isFolder=False, totalItems=totalItems )
            xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)          

    def listEpisodesFromSeason(self, season_id, serial_url):
        url = apiBase + serial_url + "?season=" + season_id
        r = requests.get(url)
        data = r.json()
        if len(data['items']) > 0:
            xbmcplugin.setContent(addon_handle, 'episodes')
            xbmcplugin.setPluginCategory(addon_handle,buildDirectoryName(data))
            for episode in data['items']:
                if self.showPremium or not "isPremium" in episode or episode["isPremium"] == False:
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    if not "videoId" in episode:
                        continue
                    videoId = episode['videoId']
                    fID = serial_url.split('/')[-1]
                    if plotEnabled:
                        url = "{}/{}/{}?episodeId={}".format(apiBase, "module/teaserrow/format/highlight",fID, videoId)
                        r = requests.get(url)
                        data = r.json()
                        if "items" in data and len(data["items"]) > 0:
                            epData = data["items"][0]
                        else:
                            epData = episode

                    else:
                        epData = episode
                    info = self.getInfoLabel(epData)
                    epName, info = getEpName(episode, info)
                    info['title'] = epName
                    li.setInfo('video', info)
                    li.setLabel(epName)
                    artDict = {}
                    artDict['icon'] = formatImageURL.replace("{fid}",str(fID))
                    if "id" in episode:
                        artDict['poster'] = episodeImageURL.replace("{eid}",str(episode['id']))
                    li.setArt(artDict)
                    url = common.build_url({'action': 'playVod', 'vod_url': episode["videoId"]})
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                listitem=li, isFolder=False)
            xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)   

    def listSearchResult(self, query):
        url = "{}/search/{}".format(apiBase, ul.quote(query))
        r = requests.get(url)
        data = r.json()
        for item in data["items"]:
            if "url" in item and "title" in item:
                url = common.build_url({'action': 'listPage'.encode('utf-8'), 'id': item['url'].encode('utf-8')})
                li = xbmcgui.ListItem(item['title'])
                sid = item['url'].split("-")[-1]
                imgurl = formatImageURL.replace("{fid}",str(sid))
                li.setArt({'poster': imgurl, 'icon' : icon_file})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def listSeasonsFromserial(self, serial_url):
        modulUrl = ""
        clean_title = "<No Title>"
        movieMetadata = False
        movieMetadataURL = -1
        movieID = -1
        url = apiBase + "/page" + serial_url
        r = requests.get(url)
        data = r.json()
        serial_url = ""
        if "title" in data:
            clean_title = data['title'].replace("im Online Stream ansehen | TVNOW","")
            xbmcplugin.setPluginCategory(addon_handle, clean_title)



        for module in data["modules"]:
            if module["moduleLayout"] == "default":
                movieID = module["id"]
            if module["moduleLayout"] == "format_season_navigation" :
                modulUrl = module["moduleUrl"]
            elif module["moduleLayout"] == "format_episode":
                serial_url = module["moduleUrl"]
            if module["moduleLayout"] == "moviemetadata":
                movieMetadata = True
                movieMetadataURL = module["moduleUrl"]

        if "id" in data:
            serial_id = data["id"]

            if modulUrl != "" and serial_url != "":
                xbmcplugin.setContent(addon_handle, 'seasons')
                url = apiBase + modulUrl
                r = requests.get(url)
                nav_data = r.json()

                for items in nav_data["items"]:
                    if "months" in items and "year" in items:
                        for month in reversed(items["months"]):
                            url = common.build_url({'action': 'listSeasonByYear', 'year': int(items['year']), 'month': month["month"] , 'id' : serial_url.encode('utf-8')})
                            label = '%s - %s - %s' % (clean_title, month["name"], items['year'])
                            li = xbmcgui.ListItem(label=label)
                            li.setProperty('IsPlayable', 'false')
                            li.setArt({'poster': formatImageURL.replace("{fid}",str(serial_id))})
                            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                            listitem=li, isFolder=True)
                    elif "season" in items:
                            url = common.build_url({'action': 'listSeason'.encode('utf-8'), 'season_id': int(items["season"]), 'id' : serial_url.encode('utf-8')})
                            label = '%s - Staffel %s' % (clean_title, items["season"])
                            li = xbmcgui.ListItem(label=label)
                            li.setProperty('IsPlayable', 'false')
                            li.setArt({'poster': formatImageURL.replace("{fid}",str(serial_id))})
                            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                            listitem=li, isFolder=True)
            elif movieMetadata != -1 and movieID != -1:
                if "title" in data:
                    title_stripped = data['title'].replace("im Online Stream | TVNOW","")
                else:
                    title_stripped = "<No Title>"
                if movieMetadata:
                    url = apiBase + movieMetadataURL
                    r = requests.get(url)
                    if r.status_code == 200:
                        data = r.json()
                    if not "headline" in data:
                        data["headline"] = title_stripped
                else:
                    if "configuration" in data and "isPremium" in data["configuration"]:
                        data["isPremium"] = data["configuration"]["isPremium"]
                    else: #Fallback
                        data["isPremium"] = False
                xbmcplugin.setPluginCategory(addon_handle, title_stripped)
                xbmcplugin.setContent(addon_handle, 'episodes')
                if self.showPremium or not "isPremium" in data or data["isPremium"] == False:
                    url = common.build_url({'action': 'playVod', 'vod_url': movieID})
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    li.setLabel('%s' % (title_stripped))
                    info = self.getInfoLabel(data, True)
                    li.setInfo('video', info)
                    li.setArt({'poster': formatImageURL.replace("{fid}",str(serial_id))})
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                listitem=li, isFolder=False)
            
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
        
