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
import tvnow
apiBase = "https://apigw.tvnow.de"
formatImageURL = "https://ais.tvnow.de/tvnow/format/{fid}_formatlogo/408x229/image.jpg"
episodeImageURL = "https://ais.tvnow.de/tvnow/movie/{eid}/408x229/image.jpg"
addon_handle = int(sys.argv[1])
icon_file = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
addon = xbmcaddon.Addon()

class Navigation():
    def __init__(self,db):
        self.db = db
        self.showPremium = (addon.getSetting('premium') == "true")
    
    def getInfoLabel(self, data, movie=False):
        info = {}
        info['title'] = data.get('headline', '') 
        if not data.get('year_of_production', '') == '':
            info['year'] = data.get('year_of_production', '')
        if movie:
            info['plot'] = data.get('description', '').replace('\n', '').strip()
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
    def setLoginPW(self):
        keyboard = xbmc.Keyboard('', 'Passwort', True)
        keyboard.doModal(60000)
        if keyboard.isConfirmed() and keyboard.getText() and len(keyboard.getText()) > 6:
            password = keyboard.getText()
            return password
        return ''
        
    def listDictCategories(self, dicttype=""):
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
        
    def listLiveTV(self):
        url = apiBase + "/module/teaserrow/epglivetv"
        r = requests.get(url)
        data = r.json()
        for item in data["items"]:
            baseJSON = item["station"][0]["now"]
            stationName = baseJSON["station"]
            stationID = baseJSON["id"]
            xbmcplugin.setPluginCategory(addon_handle, "LiveTV")
            xbmcplugin.setContent(addon_handle, 'episodes')
            if self.showPremium:
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
    
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    def listEpisodesFromSeasonByYear(self, year, month, series_url):
        url = apiBase + series_url + "?year=" + year + '&month=' + month
        r = requests.get(url)
        data = r.json()
        totalItems = len(data['items'])
        if totalItems > 0:
            listItems = []
            xbmcplugin.setContent(addon_handle, 'episodes')
            for episode in data['items']:
                if self.showPremium or episode["isPremium"] == False:
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    videoId = episode['videoId']
                    fID = series_url.split('/')[-1]
                    url = "{}/{}/{}?episodeId={}".format(apiBase, "module/teaserrow/format/highlight",fID, videoId)
                    r = requests.get(url)
                    data = r.json()
                    epData = data["items"][0]
                    info = self.getInfoLabel(epData)
                    li.setInfo('video',info)
                    li.setLabel('%s' % (episode['headline']))
                    li.setArt({'poster': episodeImageURL.replace("{eid}",str(episode['id']))})
                    url = common.build_url({'action': 'playVod', 'vod_url': episode["videoId"]})
                    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                                listitem=li, isFolder=False, totalItems=totalItems )
            xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)          

    def listEpisodesFromSeason(self, season_id, series_url):
        url = apiBase + series_url + "?season=" + season_id
        r = requests.get(url)
        data = r.json()
        if len(data['items']) > 0:
            xbmcplugin.setContent(addon_handle, 'episodes')
            for episode in data['items']:
                if self.showPremium or episode["isPremium"] == False:
                    li = xbmcgui.ListItem()
                    li.setProperty('IsPlayable', 'true')
                    videoId = episode['videoId']
                    fID = series_url.split('/')[-1]
                    url = "{}/{}/{}?episodeId={}".format(apiBase, "module/teaserrow/format/highlight",fID, videoId)
                    r = requests.get(url)
                    data = r.json()
                    epData = data["items"][0]
                    info = self.getInfoLabel(epData)
                    li.setLabel('%s' % (videoId))
                    li.setInfo('video', info)
                    li.setLabel(info['title'])
                    li.setArt({'poster': episodeImageURL.replace("{eid}",str(episode['id']))})
                    url = common.build_url({'action': 'playVod', 'vod_url': episode["videoId"]})
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
        temp = data["title"].split("-")
        #remove TVNOW and other stuff from title
        clean_title = "".join(temp[0:-1])
        xbmcplugin.setPluginCategory(addon_handle, clean_title)
        
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
            url = apiBase + "/module/moviemetadata/" + str(series_id)
            r = requests.get(url)
            data = r.json()
            title_stripped = data['title'].replace("im Online Stream | TVNOW","")
            xbmcplugin.setPluginCategory(addon_handle, title_stripped)
            xbmcplugin.setContent(addon_handle, 'episodes')
            if self.showPremium or data["isPremium"] == False:
                url = common.build_url({'action': 'playVod', 'vod_url': movieID})
                li = xbmcgui.ListItem()
                li.setProperty('IsPlayable', 'true')
                li.setLabel('%s' % (title_stripped))
                info = self.getInfoLabel(data, True)
                li.setInfo('video', info)
                li.setArt({'poster': formatImageURL.replace("{fid}",str(series_id))})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                            listitem=li, isFolder=False)
            
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
        
    