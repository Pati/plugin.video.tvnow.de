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

import xbmc
import xbmcgui
import xbmcaddon, xbmcplugin
import inputstreamhelper

from common import encode, decode, getInputstreamAddon

class TvNow:
    """TvNow Class"""

    def __init__(self):
        self.tokenset = False
        self.usingAccount = False
        self.licence_url = 'https://widevine.tvnow.de/index/proxy/|User-Agent=Dalvik%2F2.1.0%20(Linux;%20U;%20Android%207.1.1)&x-auth-token={TOKEN}|R{SSM}|'
        self.addon = xbmcaddon.Addon()
        self.username = self.addon.getSetting('email')
        self.password_old = self.addon.getSetting('password')
        self.datapath = xbmc.translatePath(self.addon.getAddonInfo('profile'))
        self.token = self.addon.getSetting('acc_token')
        self.hdEnabled = self.addon.getSetting('hd_enabled') == "true"
        self.helperActivated  = self.addon.getSetting('is_helper_enabled') == "true"
        self.patchManifest = self.addon.getSetting('patch_manifest') == "true"

        # Create session with old cookies
        self.session = requests.session()
        self.session.headers.setdefault('User-Agent','Dalvik/2.1.0 (Linux; U; Android 7.1.1)')
        self.session.headers.setdefault('Referer','https://www.tvnow.de/')
        self.session.headers.setdefault('Origin','https://www.tvnow.de/')

        if self.password_old != "":
            encpassword = encode(self.password_old)
            password = self.password_old
            self.addon.setSetting('password_enc', encpassword)
            self.addon.setSetting('password', "")
            self.sendLogin(self.username, password)

        if self.token != "":
            self.tokenset = True
            self.session.headers.setdefault('x-auth-token', self.token )
        else:
            self.login()
        
    def getToken(self, data):
        if not "pageConfig" in data or not "user" in data["pageConfig"] or not "jwt" in data["pageConfig"]["user"]:
            xbmcgui.Dialog().notification('Fehler GetToken', 'Token not found', icon=xbmcgui.NOTIFICATION_ERROR)
            return False
        self.token = data["pageConfig"]["user"]["jwt"]
        return True

    def checkPremium(self):
        base64Parts = self.token.split(".")
        token = "%s==" % base64Parts[1]
        userData = json.loads(base64.b64decode(token))
        if "roles" in userData and "premium" in userData["roles"]:
            self.addon.setSetting('premium', "true")
        elif "subscriptionState" in userData and (userData["subscriptionState"]==5 or userData["subscriptionState"]==4):
            self.addon.setSetting('premium', "true")
        if "permissions" in userData:
            if "vodPremium" in userData["permissions"] and userData["permissions"]["vodPremium"]==True:
                self.addon.setSetting('premium', "true")
            if "livePay" in userData["permissions"] and userData["permissions"]["livePay"]==True:
                self.addon.setSetting('livePay', "true")
            if "liveFree" in userData["permissions"] and userData["permissions"]["liveFree"]==True:
                self.addon.setSetting('liveFree', "true")

    def isLoggedIn(self):
        """Check if User is still logged in with the old Token"""
        if not self.tokenset or self.username == "":
            return False
        loggedIn = False
        base64Parts = self.token.split(".")
        token = "%s==" % base64Parts[1]
        userData = json.loads(base64.b64decode(token))

        if "licenceEndDate" in userData:
            licenceEndDate = userData["licenceEndDate"].split("+")[0]
            try:
                licenceEndDateTS = time.mktime(datetime.datetime.strptime(licenceEndDate, '%Y-%m-%dT%H:%M:%S').timetuple())
                if licenceEndDateTS < (time.time() + 60*60*24):
                    loggedIn = False
            except:
                loggedIn = False
        else:
            loggedIn = False
        if loggedIn and "exp" in userData and userData["exp"] > (time.time() + 60*60*24):
            self.checkPremium()
        else:
            loggedIn = False
        return loggedIn
        '''r = self.session.get('https://api.tvnow.de/v3/backend/login?fields=%5B%22id%22,%20%22token%22,%20%22user%22,%5B%22agb%22%5D%5D')
        #Parse json
        response = json.loads(r.text)
        if r.status_code == 200 and "token" in response:
            self.token = response["token"]
            self.session.headers.setdefault('x-auth-token', self.token)
            addon.setSetting('acc_token', self.token)
            self.checkPremium()
            return True
        self.session.headers.setdefault('x-auth-token', "")
        addon.setSetting('acc_token', "")
        return False'''

    def sendLogin(self, username, password):
        jlogin = { "email" : username, "password": password}
        r = self.session.post("https://auth.tvnow.de/login", json=jlogin)
        #Parse json
        response = r.text
        response = json.loads(response)
        statuscode = r.status_code
        if statuscode != 200:
            xbmc.log("Login Error: {}".format(response), level=xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Login Fehler', 'Login fehlgeschlagen. Bitte Login Daten ueberpruefen', icon=xbmcgui.NOTIFICATION_ERROR)
            return False
        elif "token" in response:
            self.token = response["token"]
            self.tokenset = True
            self.session.headers.setdefault('x-auth-token', response["token"])
            self.usingAccount = True
            self.addon.setSetting('acc_token', self.token)

            self.checkPremium()
            encpassword = encode(password)
            self.addon.setSetting('email', username)
            self.addon.setSetting('password_enc', encpassword)
            return True

    def login(self):
        self.addon.setSetting('premium', "false")
        self.addon.setSetting('livePay', "false")
        self.addon.setSetting('liveFree', "false")
        # If already logged in and active session everything is fine
        if not self.isLoggedIn():
            password = decode(self.addon.getSetting('password_enc'))
            self.usingAccount = False
            if self.username != "" and password != "":
                return self.sendLogin(self.username, password)
        else:
            return True
        # If any case is not matched return login failed
        return False

    def getPlayBackUrl(self, assetID, loggedIn, live = False):
        if live:
            url = "https://bff.apigw.tvnow.de/module/player/epg/%d?drm=1" % int(assetID)
        else:
            url = "https://bff.apigw.tvnow.de/module/player/%d" % int(assetID)
        r = self.session.get(url)
        data = r.json()
        drmProtected = False
        if "videoConfig" in data and "videoSource" in data["videoConfig"]:
            if "drm" in data["videoConfig"]["videoSource"]:
                drmProtected = True
            if drmProtected and not loggedIn:
                self.getToken(data)
            if "streams" in data["videoConfig"]["videoSource"]:
                if "dashHdUrl" in data["videoConfig"]["videoSource"]["streams"] and self.hdEnabled:
                    return data["videoConfig"]["videoSource"]["streams"]["dashHdUrl"], drmProtected
                if "dashUrl" in data["videoConfig"]["videoSource"]["streams"]: # Fallback
                    return data["videoConfig"]["videoSource"]["streams"]["dashUrl"], drmProtected
        return "", drmProtected


    def play(self, assetID, live=False):
        loggedIn = self.login()
        # Prepare new ListItem to start playback
        playBackUrl, drmProtected = self.getPlayBackUrl(assetID, loggedIn, live)
        if playBackUrl != "":
            li = xbmcgui.ListItem()
            protocol = 'mpd'
            drm = 'com.widevine.alpha'
            # Inputstream settings
            if self.helperActivated and drmProtected:
                is_helper = inputstreamhelper.Helper(protocol, drm=drm)
                if is_helper.check_inputstream():
                    is_addon = is_helper.inputstream_addon
            else:
                is_addon = getInputstreamAddon()
                if not is_addon:
                    xbmcgui.Dialog().notification('TvNow Fehler', 'Inputstream Addon fehlt!', xbmcgui.NOTIFICATION_ERROR, 2000, True)
                    return False
            if drmProtected:
                li.setProperty(is_addon + '.license_type', drm)
                if self.patchManifest:
                    playBackUrl = "http://localhost:42467/?id={}&live={}".format(assetID, 1 if live == True else 0)
            li.setProperty(is_addon + '.license_key', self.licence_url.replace("{TOKEN}",self.token))
            li.setProperty(is_addon + '.manifest_type', protocol)
            if live:
                li.setProperty(is_addon + '.manifest_update_parameter',  "full")
            li.setProperty('inputstream', is_addon)
            li.setPath(playBackUrl)
            # Start Playing
            addon_handle = int(sys.argv[1])
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)
        else:
            xbmcgui.Dialog().notification('Abspielen fehlgeschlagen', 'Es ist keine AbspielURL vorhanden', icon=xbmcgui.NOTIFICATION_ERROR)

