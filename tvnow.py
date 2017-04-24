import sys
import base64
import struct

import requests
import json
import re
import datetime
import time
import pickle
import os
import xml.etree.ElementTree as ET

import xbmc
import xbmcgui
import xbmcaddon, xbmcplugin


licence_url = 'https://widevine.rtl.de/index/proxy/|User-Agent=Dalvik%2F2.1.0%20(Linux;%20U;%20Android%207.1.1)&Content-Type=application/x-www-form-urlencoded&x-auth-token={TOKEN}|R{SSM}|'
addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
username = addon.getSetting('email')
password = addon.getSetting('password')
datapath = xbmc.translatePath(addon.getAddonInfo('profile'))
tokenPath = datapath + 'TOKEN'

# Get installed inputstream addon
def getInputstreamAddon():
    is_types = ['inputstream.adaptive', 'inputstream.smoothstream']
    for i in is_types:
        r = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "Addons.GetAddonDetails", "params": {"addonid":"' + i + '", "properties": ["enabled"]}}')
        data = json.loads(r)
        if not "error" in data.keys():
            if data["result"]["addon"]["enabled"] == True:
                return i
        
    return None

class TvNow:
    """TvNow Class"""

    entitlements = []


    def __init__(self):
        self.sessionId = ''
        self.tokenPath = tokenPath
        self.licence_url = licence_url
        self.tokenset = False
        self.token = ''

        # Create session with old cookies
        self.session = requests.session()
        self.session.headers.setdefault('User-Agent','Dalvik/2.1.0 (Linux; U; Android 7.1.1)')

        if os.path.isfile(tokenPath):
            with open(tokenPath) as f:
                self.session.headers.setdefault('x-auth-token', pickle.load(f))
                self.tokenset = True
        return


    def isLoggedIn(self):
        """Check if User is still logged in with the old Token"""
        if not self.tokenset:
            return False
        r = self.session.get('https://api.tvnow.de/v3/backend/login?fields=[%22id%22,%20%22token%22,%20%22user%22,[%22agb%22]]')
        #Parse json
        response = json.loads(r.text)

        print response

        if r.status_code == 200 and "token" in response:
            print "User still logged in"
            return True
        return False


    def sendLogin(self, username, password):
        # Try to login
        jlogin = { "email" : username, "password": password}
        r = self.session.post("https://api.tvnow.de/v3/backend/login?fields=[%22id%22,%20%22token%22,%20%22user%22,[%22agb%22]]", json=jlogin)
        #Parse jsonp
        response = r.text
        response = json.loads(response)
        print response
        return r.status_code,response
        

    def login(self):
        # If already logged in and active session everything is fine
        if not self.isLoggedIn():
            statuscode , response = self.sendLogin(username, password)
            if statuscode != 200:
                xbmcgui.Dialog().notification('Login Fehler', 'Login fehlgeschlagen. Bitte Login Daten ueberpruefen', icon=xbmcgui.NOTIFICATION_ERROR)
                return False
            elif "token" in response:
                self.token = response["token"]
                self.tokenset = True
                self.session.headers.setdefault('x-auth-token', response["token"])
                return True
        else:
            return True

        # If any case is not matched return login failed
        return False

    def play(self, manifest_url):
        if self.login():
            # Prepare new ListItem to start playback
            li = xbmcgui.ListItem(path=manifest_url)
            # Inputstream settings
            is_addon = getInputstreamAddon()
            if not is_addon:
                xbmcgui.Dialog().notification('TvNow Fehler', 'Inputstream Addon fehlt!', xbmcgui.NOTIFICATION_ERROR, 2000, True)
                return False
            li.setProperty(is_addon + '.license_type', 'com.widevine.alpha')
            li.setProperty(is_addon + '.manifest_type', 'mpd')
            li.setProperty(is_addon + '.license_key', self.licence_url.replace("{TOKEN}",self.token))
            li.setProperty('inputstreamaddon', is_addon)
            # Start Playing
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)
            

