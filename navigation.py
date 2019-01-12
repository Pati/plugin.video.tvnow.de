#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import requests
import urllib2
import json
import datetime
import time
import resources.lib.common as common
from sendung import Sendung
formatSeasondetailURL = "https://api.tvnow.de/v3/movies/formatTabPage/{fid}?fields=%5B%22id%22%2C%22episode%22%2C%22season%22%2C%22title%22%2C%22articleShort%22%2C%22isDrm%22%2C%22free%22%2C%22broadcastPreviewStartDate%22%2C%22broadcastStartDate%22%2C%22availableDate%22%2C%22duration%22%2C%22aspectRatio%22%2C%22dontCall%22%2C%22cornerLogo%22%2C%22productPlacementType%22%2C%22timeType%22%2C%22videoPlazaTags%22%2C%22alternateBroadcastDateText%22%2C%22blockadeText%22%2C%22pictures%22%2C%5B%22default%22%2C%22portrait%22%5D%2C%22manifest%22%2C%5B%22hls%22%2C%22dash%22%5D%2C%22format%22%2C%5B%22id%22%2C%22title%22%2C%22titleGroup%22%2C%22station%22%2C%22tabSpecialTeaserPosition%22%2C%22tabSeason%22%2C%22annualNavigation%22%2C%22formatTabs%22%2C%5B%22id%22%2C%22headline%22%2C%22emptyListText%22%5D%2C%22genres%22%2C%22szm%22%2C%22emptyListText%22%2C%22videoPlazaAdTag%22%5D%5D&filter=%7B%7D&order=BroadcastStartDate%20desc&maxPerPage=30"
formatSeasondetailYearURL="https://api.tvnow.de/v3/movies?fields=*,format,paymentPaytypes,pictures,trailers,packages&filter={%22BroadcastStartDate%22:{%22between%22:{%22start%22:%22{year}-01-01%2000:00:00%22,%22end%22:%20%22{year}-12-31%2023:59:59%22}},%20%22FormatId%22%20:%20{fid}}&maxPerPage=3000&order=BroadcastStartDate%20asc"
formatdetailURL = "https://api.tvnow.de/v3/formats/{fid}/movies/nownext?type=next&fields=%5B%22id%22%2C%22episode%22%2C%22season%22%2C%22title%22%2C%22articleShort%22%2C%22broadcastPreviewStartDate%22%2C%22broadcastStartDate%22%2C%22availableDate%22%2C%22duration%22%2C%22aspectRatio%22%2C%22dontCall%22%2C%22cornerLogo%22%2C%22productPlacementType%22%2C%22timeType%22%2C%22videoPlazaTags%22%2C%22alternateBroadcastDateText%22%2C%22blockadeText%22%2C%22pictures%22%2C%5B%22default%22%2C%22portrait%22%5D%2C%22manifest%22%2C%5B%22hls%22%2C%22dash%22%5D%2C%22format%22%2C%5B%22id%22%2C%22title%22%2C%22titleGroup%22%2C%22station%22%2C%22tabSpecialTeaserPosition%22%2C%22tabSeason%22%2C%22annualNavigation%22%2C%22formatTabs%22%2C%5B%22id%22%2C%22headline%22%2C%22emptyListText%22%5D%2C%22genres%22%2C%22szm%22%2C%22emptyListText%22%2C%22videoPlazaAdTag%22%5D%5D"
#formatdetailURL = "https://api.tvnow.de/v3/formats/{fid}?fields=%5B%*,.*,formatTabs.*,formatTabs.headline,annualNavigation.*5D"
formatImageURL = "https://ais.tvnow.de/tvnow/format/{fid}_formatlogo/408x229/image.jpg"
episodeImageURL = "https://ais.tvnow.de/tvnow/movie/{eid}/408x229/image.jpg"
addon_handle = int(sys.argv[1])
icon_file = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
addon = xbmcaddon.Addon()
username = addon.getSetting('email')
password = addon.getSetting('password')

class Navigation():
    def __init__(self,db):
        self.db = db
        self.showPremium = (username != "" and password != "")
    def listDictCategories(self, dicttype=""):
        print(sys.argv)
        d = self.db.getDict(dicttype)
        for item in sorted(d.keys()):
            url = common.build_url({'action': 'listDict', 'id': item, 'dict' : dicttype})
            li = xbmcgui.ListItem(item, iconImage=icon_file)
            #li.setArt({'poster': formatImageURL.replace("{fid}",str(item["id"]))})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
    def listDict(self, dictkey,dicttype=""):
        d = self.db.getDict(dicttype)
        for item in d[dictkey]:
            url = common.build_url({'action': 'listPage', 'id': item.sid})
            li = xbmcgui.ListItem(item.title, iconImage=icon_file)
            imgurl = formatImageURL.replace("{fid}",str(item.sid))
            li.setArt({'poster': imgurl})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def rootDir(self):       
        url = common.build_url({'action': 'listDictCats', 'id': 'Az'})
        li = xbmcgui.ListItem()
        li.setLabel('Sendungen A-Z')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                   listitem=li, isFolder=True)
        url = common.build_url({'action': 'listDictCats', 'id': 'cat'})
        li = xbmcgui.ListItem()
        li.setLabel('Sendungen nach Kategorien')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                   listitem=li, isFolder=True)
        url = common.build_url({'action': 'listDictCats', 'id': 'station'})
        li = xbmcgui.ListItem()
        li.setLabel('Sendungen nach Sender')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                   listitem=li, isFolder=True)
    
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def listEpisodesFromSeasonByYear(self, year, series_id):
        pages = 1
        i = 0
        base_url = formatSeasondetailYearURL.replace("{fid}", str(series_id)).replace("{year}", str(year))
        print base_url
        while i < pages:
            url = "%s&page=%d" % (base_url, i+1)
            r = requests.get(url)
            data = r.json()
            pages = (data["total"] // 30) + 1
            xbmcplugin.setContent(addon_handle, 'episodes')
            for episode in data['items']:
                if not "manifest" in episode or not "dash" in episode["manifest"]:
                    continue
                if self.showPremium or episode["free"]:
                    url = common.build_url({'action': 'playVod', 'vod_url': episode["manifest"]['dash']})
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    info = self.getInfoLabel('Episode', episode)
                    li.setInfo('video', info)
                    li.setLabel('%02d. %s' % (int(info['episode']), info['title']))
                    li.setArt({'poster': episodeImageURL.replace("{eid}",str(episode['id']))})
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                listitem=li, isFolder=False)
            i += 1
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)   
    def listEpisodesFromSeason(self, season_id):
        pages = 1
        i = 0
        base_url = formatSeasondetailURL.replace("{fid}", str(season_id))
        while i < pages:
            url = "%s&page=%d" % (base_url, i+1)
            r = requests.get(url)
            data = r.json()
            pages = (data["total"] // 30) + 1
            xbmcplugin.setContent(addon_handle, 'episodes')
            for episode in data['items']:
                if not "manifest" in episode or not "dash" in episode["manifest"]:
                    continue
                if self.showPremium or episode["free"]:
                    url = common.build_url({'action': 'playVod', 'vod_url': episode["manifest"]['dash']})
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    info = self.getInfoLabel('Episode', episode)
                    li.setInfo('video', info)
                    li.setLabel('%02d. %s' % (int(info['episode']), info['title']))
                    li.setArt({'poster': episodeImageURL.replace("{eid}",str(episode['id']))})
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                listitem=li, isFolder=False)
            i += 1
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)   

    def listSeasonsFromSeries(self, series_id):
        url = formatdetailURL.replace("{fid}", str(series_id))
        r = requests.get(url)
        data = r.json()["format"]
        xbmcplugin.setContent(addon_handle, 'seasons')
        if len(data["annualNavigation"]["items"]) > 1:
            for annual in data['annualNavigation']["items"]:
                print(annual)
                url = common.build_url({'action': 'listSeasonByYear', 'year': annual['year'], 'id': series_id})
                label = '%s - %s' % (data["title"], annual['year'])
                li = xbmcgui.ListItem(label=label)
                li.setProperty('IsPlayable', 'false')
                li.setArt({'poster': formatImageURL.replace("{fid}",str(series_id))})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                listitem=li, isFolder=True)
        else:
            if len(data['formatTabs']["items"]) == 1:
                return self.listEpisodesFromSeason(data['formatTabs']["items"][0]["id"])
            else:
                for season in data['formatTabs']["items"]:
                    print(season)
                    url = common.build_url({'action': 'listSeason', 'id': season['id']})
                    label = '%s - %s' % (data["title"], season['headline'])
                    li = xbmcgui.ListItem(label=label)
                    li.setProperty('IsPlayable', 'false')
                    li.setArt({'poster': formatImageURL.replace("{fid}",str(series_id))})
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                    listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
        
    def getInfoLabel(self, asset_type, data):
        info = {}
        info['title'] = data.get('title', '')
        if not data.get('year_of_production', '') == '':
            info['year'] = data.get('year_of_production', '')
        info['plot'] = data.get('articleShort', '').replace('\n', '').strip()
        if 'duration' in data:
            duration = time.strptime(data['duration'], "%H:%M:%S")
            info['duration'] = duration.tm_hour * 3600 + duration.tm_min * 60 + duration.tm_sec
        else:
            info['duration'] = 0
        if asset_type == 'Episode':
            info['mediatype'] = 'episode'
            info['episode'] = data.get('episode', '')           
            info['season'] = data.get('season', '')
            info['tvshowtitle'] = data["format"].get('title', '')
            if info['title'] == '':
                info['title'] = '%s - S%02dE%02d' % (data.get('serie_title', ''), data.get('season_nr', 0), data.get('episode_nr', 0))
            else:
                info['title'] = '%02d - %s' % (info['episode'], info['title'])
        return info