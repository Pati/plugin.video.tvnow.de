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
from common import build_url, parseDateTime
from sendung import Sendung
import tvnow
apiBase = "https://bff.apigw.tvnow.de"
formatImageURL = ("https://ais.tvnow.de/tvnow/format/{fid}_formatlogo/408x229/"
    + "image.jpg")
episodeImageURL = "https://ais.tvnow.de/tvnow/movie/{eid}/408x229/image.jpg"
addon_handle = int(sys.argv[1])
try:
    #py2
    icon_file = xbmc.translatePath(
        xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
except:
    icon_file = xbmc.translatePath(
        xbmcaddon.Addon().getAddonInfo('path')+'/icon.png')
addon = xbmcaddon.Addon()
plotEnabled = addon.getSetting('plot_enabled') == "true"

class Navigation():
    @staticmethod
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

    @staticmethod
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
            if "teaserSeason" in ecommerce:
                match = re.search(r'(\d+)', ecommerce["teaserSeason"])
                if match:
                    info['season'] = match.group(1)
            if "teaserEpisodeNumber" in ecommerce:
                epNamePrefix =  ecommerce["teaserEpisodeNumber"]
                match = re.search(r'(\d+)', ecommerce["teaserEpisodeNumber"])
                if match:
                    info['episode'] = match.group(1)
            if "teaserEpisodeName" in ecommerce:
                epName = ecommerce["teaserEpisodeName"]
                info['title'] = ecommerce["teaserEpisodeName"]
            elif "teaserName" in ecommerce:
                epName = ecommerce["teaserName"]
                info['title'] = ecommerce["teaserName"]
            if "teaserFormatName" in ecommerce:
                info['tvShowTitle'] = ecommerce["teaserFormatName"]
            if "type" in episode and episode["type"].lower() == "serie":
                info['mediatype'] = "episode"
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

    @staticmethod
    def _getInfoLabel(data, movie=False):
        info = {}
        info['title'] = data.get('headline', '')
        if not data.get('year_of_production', '') == '':
            info['year'] = data.get('year_of_production', '')
        if movie:
            if "description" in data:
                info['plot'] = data.get(
                    'description', '').replace('\n', '').strip()
            elif "seo" in data:
                info['plot'] = data["seo"].get(
                    'text', '').replace('\n', '').strip()
                info['plot'] = re.sub('<[^<]+?>', '', info['plot'])
        else:
            info['plot'] = data.get('text', '').replace('\n', '').strip()
        return info

    def _setLoginPW(self):
        keyboard = xbmc.Keyboard('', 'Passwort', True)
        keyboard.doModal(60000)
        if (keyboard.isConfirmed() and keyboard.getText() and
            len(keyboard.getText()) >= 6):
            password = keyboard.getText()
            return password
        return ''

    def __init__(self, db):
        self._db = db
        self._showPremium = (addon.getSetting('premium') == "true")
        self._showlive = (addon.getSetting('liveFree') == "true")
        self._showLivePay = (addon.getSetting('livePay') == "true")

    def login(self):
        keyboard = xbmc.Keyboard('', 'E-Mail-Adresse')
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            username = keyboard.getText()
            password = self._setLoginPW()
            if password != '': 
                TvNow = tvnow.TvNow()
                if TvNow.sendLogin(username, password):
                    xbmcgui.Dialog().notification(
                        'Login erfolgreich', 'Angemeldet als "'
                        + username + '".', icon=xbmcgui.NOTIFICATION_INFO)
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

    def listDictCategories(self, dicttype=""):
        d = self._db.getDict(dicttype)
        for item in sorted(d.keys()):
            url = build_url({
                'action': 'listDict',
                'id': item,
                'dict' : dicttype})
            li = xbmcgui.ListItem(item)
            li.setArt({'icon': icon_file})
            xbmcplugin.addDirectoryItem(
                handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def listDict(self, dictkey,dicttype=""):
        d = self._db.getDict(dicttype)
        for item in d[dictkey]:
            url = build_url({'action': 'listPage', 'id': item.sid})
            li = xbmcgui.ListItem(item.title)
            sid = item.sid.split("-")[-1]
            imgurl = formatImageURL.replace("{fid}",str(sid))
            li.setArt({'poster': imgurl, 'icon': icon_file})
            xbmcplugin.addDirectoryItem(
                handle=addon_handle, url=url, listitem=li, isFolder=True)
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
                if self._showlive and (payTV == False or self._showLivePay):
                    url = build_url({
                        'action': 'playLive',
                        'vod_url': stationID})
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    li.setInfo('video', "")
                    li.setLabel('%s' % (stationName))
                    li.setArt({'poster': baseJSON["image"][0]["src"]})
                    xbmcplugin.addDirectoryItem(
                        handle=addon_handle, url=url, listitem=li,
                        isFolder=False)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def rootDir(self):
        url = build_url({'action': 'listDictCats', 'id': 'Az'})
        li = xbmcgui.ListItem()
        li.setLabel('Sendungen A-Z')
        xbmcplugin.addDirectoryItem(
            handle=addon_handle, url=url, listitem=li, isFolder=True)
        url = build_url({'action': 'listDictCats', 'id': 'station'})
        li = xbmcgui.ListItem()
        li.setLabel('Sendungen nach Sender')
        xbmcplugin.addDirectoryItem(
            handle=addon_handle, url=url, listitem=li, isFolder=True)
        url = build_url({'action': 'listLive'})
        li = xbmcgui.ListItem()
        li.setLabel('LiveTV')
        xbmcplugin.addDirectoryItem(
            handle=addon_handle, url=url, listitem=li, isFolder=True)

        url = build_url({'action': 'search'})
        li = xbmcgui.ListItem()
        li.setLabel('Suche')
        xbmcplugin.addDirectoryItem(
            handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def listEpisodesFromSeasonByYear(self, year, month, serial_url):
        url = apiBase + serial_url + "?year=" + year + '&month=' + month
        r = requests.get(url)
        data = r.json()
        totalItems = len(data['items'])
        if totalItems > 0:
            xbmcplugin.setContent(addon_handle, 'EPISODES')
            xbmcplugin.setPluginCategory(
                addon_handle, Navigation.buildDirectoryName(data))
            for episode in data['items']:
                if self._showPremium or episode["isPremium"] == False:
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    videoId = episode['videoId']
                    fID = serial_url.split('/')[-1]
                    if plotEnabled:
                        url = "{}/{}/{}?episodeId={}".format(
                            apiBase, "module/teaserrow/format/highlight",
                            fID, videoId)
                        r = requests.get(url)
                        data = r.json()
                        epData = data["items"][0]
                    else:
                        epData = episode
                    info = self._getInfoLabel(epData)
                    epName, info = Navigation.getEpName(episode, info)
                    li.setInfo('video',info)
                    li.setLabel('%s' % (epName))
                    li.setArt({
                        'poster': episodeImageURL.replace(
                            "{eid}", str(episode['id'])),
                        'clearlogo': formatImageURL.replace(
                            "{fid}", str(fID))})
                    url = build_url({
                        'action': 'playVod',
                        'vod_url': episode["videoId"]})
                    xbmcplugin.addDirectoryItem(
                        handle=addon_handle, url=url, listitem=li,
                        isFolder=False, totalItems=totalItems)
            xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def listEpisodesFromSeason(self, season_id, serial_url):
        url = apiBase + serial_url + "?season=" + season_id
        r = requests.get(url)
        data = r.json()
        if len(data['items']) > 0:
            xbmcplugin.setContent(addon_handle, 'episodes')
            xbmcplugin.setPluginCategory(
                addon_handle, Navigation.buildDirectoryName(data))
            for episode in data['items']:
                if (self._showPremium or not "isPremium" in episode or
                    episode["isPremium"] == False):
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    if not "videoId" in episode:
                        continue
                    videoId = episode['videoId']
                    fID = serial_url.split('/')[-1]
                    if plotEnabled:
                        url = "{}/{}/{}?episodeId={}".format(
                            apiBase, "module/teaserrow/format/highlight",
                            fID, videoId)
                        r = requests.get(url)
                        data = r.json()
                        if "items" in data and len(data["items"]) > 0:
                            epData = data["items"][0]
                        else:
                            epData = episode
                    else:
                        epData = episode
                    info = self._getInfoLabel(epData)
                    epName, info = Navigation.getEpName(episode, info)
                    li.setInfo('video', info)
                    li.setLabel(epName)
                    artDict = {}
                    artDict['icon'] = formatImageURL.replace("{fid}",str(fID))
                    if "id" in episode:
                        artDict['poster'] = episodeImageURL.replace(
                            "{eid}",str(episode['id']))
                    li.setArt(artDict)
                    url = build_url({
                        'action': 'playVod', 'vod_url': episode["videoId"]})
                    xbmcplugin.addDirectoryItem(
                        handle=addon_handle, url=url, listitem=li,
                        isFolder=False)
            xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def listSearchResult(self, query):
        url = "{}/search/{}".format(apiBase, ul.quote(query))
        r = requests.get(url)
        data = r.json()
        for item in data["items"]:
            if "url" in item and "title" in item:
                url = build_url({
                    'action': 'listPage', 'id': item['url']})
                li = xbmcgui.ListItem(item['title'])
                sid = item['url'].split("-")[-1]
                imgurl = formatImageURL.replace("{fid}",str(sid))
                li.setArt({'poster': imgurl, 'icon' : icon_file})
                xbmcplugin.addDirectoryItem(
                    handle=addon_handle, url=url, listitem=li, isFolder=True)
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
            clean_title = data['title'].replace(
                "im Online Stream ansehen | TVNOW","")
            xbmcplugin.setPluginCategory(addon_handle, clean_title)

        for module in data["modules"]:
            if module["moduleLayout"] == "default":
                movieID = module["id"]
            if module["moduleLayout"] == "format_season_navigation":
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
                            url = build_url({
                                'action': 'listSeasonByYear',
                                'year': int(items['year']),
                                'month': month["month"],
                                'id' : serial_url.encode('utf-8')})
                            label = "{} - {} - {}".format(
                                clean_title, month["name"], items['year'])
                            li = xbmcgui.ListItem(label=label)
                            li.setProperty('IsPlayable', 'false')
                            li.setArt({
                                'poster': formatImageURL.replace(
                                    "{fid}", str(serial_id))})
                            xbmcplugin.addDirectoryItem(
                                handle=addon_handle, url=url, listitem=li,
                                isFolder=True)
                    elif "season" in items:
                            url = build_url({
                                'action': 'listSeason',
                                'season_id': items["season"],
                                'id' : serial_url})
                            label = "{} - Staffel {}".format(
                                clean_title, items["season"])
                            li = xbmcgui.ListItem(label=label)
                            li.setProperty('IsPlayable', 'false')
                            li.setArt({
                                'poster': formatImageURL.replace(
                                    "{fid}", str(serial_id))})
                            xbmcplugin.addDirectoryItem(
                                handle=addon_handle, url=url, listitem=li,
                                isFolder=True)
            elif movieMetadata != -1 and movieID != -1:
                if "title" in data:
                    title_stripped = data['title'].replace(
                        "im Online Stream | TVNOW","")
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
                    if ("configuration" in data and
                        "isPremium" in data["configuration"]):
                        data["isPremium"] = data["configuration"]["isPremium"]
                    else: #Fallback
                        data["isPremium"] = False
                xbmcplugin.setPluginCategory(addon_handle, title_stripped)
                xbmcplugin.setContent(addon_handle, 'episodes')
                if (self._showPremium or not "isPremium" in data or
                    data["isPremium"] == False):
                    url = build_url({
                        'action': 'playVod', 'vod_url': movieID})
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    li.setLabel('%s' % (title_stripped))
                    info = self._getInfoLabel(data, True)
                    li.setInfo('video', info)
                    li.setArt({'poster': formatImageURL.replace(
                        "{fid}", str(serial_id))})
                    xbmcplugin.addDirectoryItem(
                        handle=addon_handle, url=url, listitem=li,
                        isFolder=False)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
        
