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


licence_url = 'https://widevine.tvnow.de/index/proxy/|User-Agent=Dalvik%2F2.1.0%20(Linux;%20U;%20Android%207.1.1)&x-auth-token={TOKEN}|R{SSM}|'
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
        self.usingAccount = False

        # Create session with old cookies
        self.session = requests.session()
        self.session.headers.setdefault('User-Agent','Dalvik/2.1.0 (Linux; U; Android 7.1.1)')

        if os.path.isfile(tokenPath):
            with open(tokenPath) as f:
                self.session.headers.setdefault('x-auth-token', pickle.load(f))
                self.tokenset = True
        return
        
    def getToken(self):
        baseEndPoint = "https://www.tvnow.de/"
        endPoint = baseEndPoint
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0"}
        r = requests.get(endPoint,headers=headers)
        m = re.search(r'<script type="text/javascript" src="(main\.[A-z0-9]+\.js)">', r.text)
        jsName = ""
        if m:
            jsName = m.group(1)
        else:
            xbmcgui.Dialog().notification('Fehler GetToken', 'JS not found', icon=xbmcgui.NOTIFICATION_ERROR)
            return "0"
            
        endPoint = baseEndPoint + '/' + jsName
        r = requests.get(endPoint,headers=headers)
        m = re.search(r'[A-z]\.prototype\.getDefaultUserdata=function\(\){return{token:"([A-z0-9.]+)"', r.text)
        if m:
            return m.group(1)
        return "0"



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
            self.usingAccount = False
            if username != "" and password != "":
                statuscode , response = self.sendLogin(username, password)
                if statuscode != 200:
                    xbmcgui.Dialog().notification('Login Fehler', 'Login fehlgeschlagen. Bitte Login Daten ueberpruefen', icon=xbmcgui.NOTIFICATION_ERROR)
                    return False
                elif "token" in response:
                    self.token = response["token"]
                    self.tokenset = True
                    self.session.headers.setdefault('x-auth-token', response["token"])
                    self.usingAccount = True
                    return True
            else:
                token = self.getToken()
                if token != "0":
                    self.token = token
                    return True
                else:
                    xbmcgui.Dialog().notification('Fehler', 'Token not found', icon=xbmcgui.NOTIFICATION_ERROR)
                    return False
        else:
            return True

        # If any case is not matched return login failed
        return False

    def getPlayBackUrl(self,assetID):
        url = "https://apigw.tvnow.de/module/player/%d" % int(assetID)
        r = self.session.get(url)
        data = r.json()
        print data
        if "manifest" in data:
            if "dashhd" in data["manifest"]:
                return data["manifest"]["dashhd"]
            if "dash" in data["manifest"]: # Fallback
                return data["manifest"]["dash"]
        return ""

    def play(self, assetID):
        if self.login():
            # Prepare new ListItem to start playback
            playBackUrl = self.getPlayBackUrl(assetID)
            if playBackUrl != "":
                li = xbmcgui.ListItem(path=playBackUrl)
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
            else:
                xbmcgui.Dialog().notification('Abspielen fehlgeschlagen', 'Es ist keine AbspielURL vorhanden', icon=xbmcgui.NOTIFICATION_ERROR)

