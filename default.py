#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import urlparse
import resources.lib.vod as vod
import os
import pickle
from navigation import Navigation
from database import Database
import xbmcaddon

addon_handle = int(sys.argv[1])
plugin_base_url = sys.argv[0]
params = dict(urlparse.parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon()
datapath = xbmc.translatePath(addon.getAddonInfo('profile'))
dbPath = datapath + 'Database'
db = Database()
if not os.path.isdir(datapath):
    os.mkdir(datapath)
if os.path.isfile(dbPath):
    with open(dbPath) as f:
        try:
            db = pickle.load(f)
        except:
            print "Invalid File"
if db.updateDatabase():
    f = file(dbPath, "wb")
    pickle.dump(db,f)

nav = Navigation(db)
# Router for all plugin actions
if params:

    print params

    if params['action'] == 'playVod':
        vod.playAsset(params['vod_url'])
    if params['action'] == 'playLive':
        vod.playLive(params['vod_url'])
    elif params['action'] == 'listPage':
        nav.listSeasonsFromSeries(params['id'])
    elif params['action'] == 'listSeason':
        nav.listEpisodesFromSeason(params['season_id'], params['id'])
    elif params['action'] == 'listDict':
        nav.listDict(params["id"], params['dict'])
    elif params['action'] == 'listDictCats':
        nav.listDictCategories(params["id"])
    elif params['action'] == 'listLive':
        nav.listLiveTV()
    elif params['action'] == 'favList':
        fav = favoriten.Favoriten()
        fav.listfav()
    elif params['action'] == 'favlistAdd':
        fav = favoriten.Favoriten()
        fav.favadd(params['url'], params['title'] , params['img'])
    elif params['action'] == 'listSeasonByYear':
        nav.listEpisodesFromSeasonByYear(params['year'], params['month'],params['id'])
else:
    nav.rootDir()
    
