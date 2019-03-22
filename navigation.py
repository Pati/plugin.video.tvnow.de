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
apiBase = "https://apigw.tvnow.de"
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
            sid = item.sid.split("-")[-1]
            imgurl = formatImageURL.replace("{fid}",str(sid))
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
        url = common.build_url({'action': 'listDictCats', 'id': 'station'})
        li = xbmcgui.ListItem()
        li.setLabel('Sendungen nach Sender')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                   listitem=li, isFolder=True)
    
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def listEpisodesFromSeasonByYear(self, year, month, series_url):
        url = apiBase + series_url + "?year=" + year + '&month=' + month
        r = requests.get(url)
        data = r.json()
        if len(data['items']) > 0:
            xbmcplugin.setPluginCategory(addon_handle, data['items'][0]["headline"])
            xbmcplugin.setContent(addon_handle, 'episodes')
            for episode in data['items']:
                if self.showPremium or episode["isPremium"] == False:
                    url = common.build_url({'action': 'playVod', 'vod_url': episode["videoId"]})
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    info = self.getInfoLabel('Episode', episode)
                    li.setInfo('video', info)
                    li.setLabel('%s' % (info['title']))
                    li.setArt({'poster': episodeImageURL.replace("{eid}",str(episode['id']))})
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                listitem=li, isFolder=False)
            xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)   

    def listEpisodesFromSeason(self, season_id, series_url):
        url = apiBase + series_url + "?season=" + season_id
        r = requests.get(url)
        data = r.json()
        if len(data['items']) > 0:
            xbmcplugin.setPluginCategory(addon_handle, data['items'][0]["headline"])
            xbmcplugin.setContent(addon_handle, 'episodes')
            for episode in data['items']:
                if self.showPremium or episode["isPremium"] == False:
                    url = common.build_url({'action': 'playVod', 'vod_url': episode["videoId"]})
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    info = self.getInfoLabel('Episode', episode)
                    li.setInfo('video', info)
                    li.setLabel(info['title'])
                    li.setArt({'poster': episodeImageURL.replace("{eid}",str(episode['id']))})
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                listitem=li, isFolder=False)
            xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)   

    def listSeasonsFromSeries(self, series_url):
        url = apiBase + "/page" + series_url
        r = requests.get(url)
        data = r.json()
        modulUrl = ""
        series_id = data["id"]
        series_url = ""
        movieID = -1
        
        
        for module in data["modules"]:
            if module["moduleLayout"] == "default":
                movieID = module["id"]
            if module["moduleLayout"] == "format_season_navigation" :
                modulUrl = module["moduleUrl"]
            elif module["moduleLayout"] == "format_episode":
                series_url = module["moduleUrl"]
            
        if modulUrl != "" and series_url != "":
            xbmcplugin.setContent(addon_handle, 'seasons')
            url = apiBase + modulUrl
            r = requests.get(url)
            nav_data = r.json()
            
            for items in reversed(nav_data["items"]):
                #remove TVNOW from title
                temp = data["title"].split("-")
                clean_title = "".join(temp[0:-1])
                if "months" in items:
                    for month in reversed(items["months"]):
                        url = common.build_url({'action': 'listSeasonByYear', 'year': items['year'], 'month': month.keys()[0] , 'id' : series_url})
                        label = '%s - %s - %s' % (clean_title, month.values()[0], items['year'])
                        li = xbmcgui.ListItem(label=label)
                        li.setProperty('IsPlayable', 'false')
                        li.setArt({'poster': formatImageURL.replace("{fid}",str(series_id))})
                        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                        listitem=li, isFolder=True)
                elif "season" in items:
                        url = common.build_url({'action': 'listSeason', 'season_id': items["season"], 'id' : series_url})
                        label = '%s - Staffel %s' % (clean_title, items["season"])
                        li = xbmcgui.ListItem(label=label)
                        li.setProperty('IsPlayable', 'false')
                        li.setArt({'poster': formatImageURL.replace("{fid}",str(series_id))})
                        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                        listitem=li, isFolder=True)
        elif movieID != -1:
            title_stripped = data['title'].replace("im Online Stream | TVNOW","")
            xbmcplugin.setPluginCategory(addon_handle, title_stripped)
            xbmcplugin.setContent(addon_handle, 'episodes')
            if self.showPremium or episode["isPremium"] == False:
                url = common.build_url({'action': 'playVod', 'vod_url': movieID})
                li = xbmcgui.ListItem()
                li.setProperty('IsPlayable', 'true')
                li.setLabel('%s' % (title_stripped))
                li.setInfo('video', '')
                li.setArt({'poster': formatImageURL.replace("{fid}",str(series_id))})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                            listitem=li, isFolder=False)
            
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
        
    def getInfoLabel(self, asset_type, data):
        info = {}
        info['title'] = data.get('subheadline', '') 
        if not data.get('year_of_production', '') == '':
            info['year'] = data.get('year_of_production', '')
        info['plot'] = data.get('text', '').replace('\n', '').strip()
        return info