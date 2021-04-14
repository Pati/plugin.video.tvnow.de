#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
try:
    #py2
    import urlparse
except:
    #py3
    import urllib.parse as urlparse
import resources.lib.vod as vod
import os
import pickle
from resources.lib.navigation import Navigation
from resources.lib.database import Database
import xbmcaddon
import xbmcvfs

addon_handle = int(sys.argv[1])
plugin_base_url = sys.argv[0]
params = dict(urlparse.parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon()
datapath = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
dbPath = datapath + 'Database'
db = Database()
if not os.path.isdir(datapath):
    os.mkdir(datapath)
if os.path.isfile(dbPath):
    with open(dbPath) as f:
        try:
            db = pickle.load(f)
        except:
            print ("Invalid File")
if db.updateDatabase():
    with open(dbPath, "wb") as f:
        pickle.dump(db,f)

nav = Navigation(db)
# Router for all plugin actions
if params:
    if params['action'] == 'playVod':
        vod.playAsset(params['vod_url'])
    if params['action'] == 'playLive':
        vod.playLive(params['vod_url'])
    elif params['action'] == 'listPage':
        nav.listSeasonsFromserial(params['id'])
    elif params['action'] == 'listSeason':
        nav.listEpisodesFromSeason(params['season_id'], params['id'])
    elif params['action'] == 'listDict':
        nav.listDict(params["id"], params['dict'])
    elif params['action'] == 'listDictCats':
        nav.listDictCategories(params["id"])
    elif params['action'] == 'listLive':
        nav.listLiveTV()
    elif params['action'] == 'login':
        nav.login()
    elif params['action'] == 'search':
        nav.search()
    #elif params['action'] == 'favList':
    #    fav = favoriten.Favoriten()
    #    fav.listfav()
    #elif params['action'] == 'favlistAdd':
    #    fav = favoriten.Favoriten()
    #    fav.favadd(params['url'], params['title'] , params['img'])
    elif params['action'] == 'listSeasonByYear':
        nav.listEpisodesFromSeasonByYear(params['year'], params['month'],params['id'])
else:
    nav.rootDir()
    
