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
from pyDes import *
import uuid
import xml.etree.ElementTree as ET

from platform import node
import xbmc
import xbmcgui
import xbmcaddon, xbmcplugin

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
    
def getmac():
    mac = uuid.getnode()
    if (mac >> 40) % 2:
        mac = node()
    return uuid.uuid5(uuid.NAMESPACE_DNS, str(mac)).bytes
    
def encode(data):
    k = triple_des(getmac(), CBC, "\0\0\0\0\0\0\0\0", padmode=PAD_PKCS5)
    d = k.encrypt(data)
    return base64.b64encode(d)

def decode(data):
    if not data:
        return ''
    k = triple_des(getmac(), CBC, "\0\0\0\0\0\0\0\0", padmode=PAD_PKCS5)
    d = k.decrypt(base64.b64decode(data))
    return d
    
licence_url = 'https://widevine.tvnow.de/index/proxy/|User-Agent=Dalvik%2F2.1.0%20(Linux;%20U;%20Android%207.1.1)&x-auth-token={TOKEN}|R{SSM}|'
addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
username = addon.getSetting('email')
password = decode(addon.getSetting('password_enc'))
password_old = addon.getSetting('password')
datapath = xbmc.translatePath(addon.getAddonInfo('profile'))
token = addon.getSetting('acc_token')
hdEnabled = addon.getSetting('hd_enabled') == "true"


class TvNow:
    """TvNow Class"""

    entitlements = []


    def __init__(self):
        self.sessionId = ''
        self.licence_url = licence_url
        self.tokenset = False
        self.token = ''
        self.usingAccount = False

        # Create session with old cookies
        self.session = requests.session()
        self.session.headers.setdefault('User-Agent','Dalvik/2.1.0 (Linux; U; Android 7.1.1)')
        
        if password_old != "":
            encpassword = encode(password_old)
            password = password_old
            addon.setSetting('password_enc', encpassword)
            addon.setSetting('password', "")
            self.sendLogin(username, password)

        if token != "":
            self.token = token
            self.tokenset = True
            self.session.headers.setdefault('x-auth-token', self.token )
        else:
            self.login()
        
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
        if r.status_code == 200 and "token" in response:
            self.token = response["token"]
            self.session.headers.setdefault('x-auth-token', self.token)
            addon.setSetting('acc_token', self.token)
            base64Parts = self.token.split(".")
            tokendata = "%s==" % base64Parts[1]
            userData = json.loads(base64.b64decode(tokendata))
            if "premium" in userData["roles"]:
                addon.setSetting('premium', "true")
            elif "subscriptionState" in userData and (userData["subscriptionState"]==5 or userData["subscriptionState"]==4):
                addon.setSetting('premium', "true")
            return True
        self.session.headers.setdefault('x-auth-token', "")
        addon.setSetting('acc_token', "")
        return False            

    def sendLogin(self, username, password):
        jlogin = { "email" : username, "password": password}
        r = self.session.post("https://api.tvnow.de/v3/backend/login?fields=[%22id%22,%20%22token%22,%20%22user%22,[%22agb%22]]", json=jlogin)
        #Parse json
        response = r.text
        response = json.loads(response)
        statuscode = r.status_code
        if statuscode != 200:
            xbmcgui.Dialog().notification('Login Fehler', 'Login fehlgeschlagen. Bitte Login Daten ueberpruefen', icon=xbmcgui.NOTIFICATION_ERROR)
            return False
        elif "token" in response:
            self.token = response["token"]
            self.tokenset = True
            self.session.headers.setdefault('x-auth-token', response["token"])
            self.usingAccount = True
            
            addon.setSetting('acc_token', self.token)
            base64Parts = self.token.split(".")
            tokendata = "%s==" % base64Parts[1]
            userData = json.loads(base64.b64decode(tokendata))
            if "premium" in userData["roles"]:
                addon.setSetting('premium', "true")
            elif "subscriptionState" in userData and (userData["subscriptionState"]==5 or userData["subscriptionState"]==4):
                addon.setSetting('premium', "true")
            encpassword = encode(password)
            addon.setSetting('email', username)
            addon.setSetting('password_enc', encpassword)
            return True
    def login(self):
        addon.setSetting('premium', "false")
        # If already logged in and active session everything is fine
        if not self.isLoggedIn():
            self.usingAccount = False
            if username != "" and password != "":
                self.sendLogin(username, password)
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

    def getPlayBackUrl(self,assetID, live = False):
        if live:
            url = "https://apigw.tvnow.de/module/player/epg/%d?drm=1" % int(assetID)
        else:
            url = "https://apigw.tvnow.de/module/player/%d" % int(assetID)
        r = self.session.get(url)
        data = r.json()
        if "manifest" in data:
            if "dashhd" in data["manifest"] and hdEnabled:
                return data["manifest"]["dashhd"]
            if "dash" in data["manifest"]: # Fallback
                return data["manifest"]["dash"]
        return ""

    def play(self, assetID, live=False):
        if self.login():
            # Prepare new ListItem to start playback
            playBackUrl = self.getPlayBackUrl(assetID,live)
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

