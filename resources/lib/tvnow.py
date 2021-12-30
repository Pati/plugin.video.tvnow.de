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
import xbmcvfs
import xbmcaddon, xbmcplugin
import inputstreamhelper

from resources.lib.common import encode, decode, getInputstreamAddon

class TvNow:
    """TvNow Class"""

    def __init__(self):
        self._tokenset = False
        self._usingAccount = False
        self._licence_url = ("{LICURL}|"
            + "User-Agent=Dalvik%2F2.1.0%20(Linux;%20U;%20Android%207.1.1)"
            + "&x-auth-token={TOKEN}|R{SSM}|")
        self._addon = xbmcaddon.Addon()
        self._username = self._addon.getSetting('email')
        self._password_old = self._addon.getSetting('password')
        self._datapath = xbmcvfs.translatePath(
            self._addon.getAddonInfo('profile'))
        self._token = self._addon.getSetting('acc_token')
        self._hdEnabled = self._addon.getSetting('hd_enabled') == "true"
        self._helperActivated = self._addon.getSetting(
            'is_helper_enabled') == "true"
        self._patchManifest = self._addon.getSetting('patch_manifest') == "true"
        self._recFile = xbmcvfs.translatePath(self._addon.getAddonInfo('profile')) + "recomendations.json"


        # Create session with old cookies
        self._session = requests.session()
        self._session.headers.setdefault(
            'User-Agent','Dalvik/2.1.0 (Linux; U; Android 7.1.1)')
        self._session.headers.setdefault('Referer','https://www.tvnow.de/')
        self._session.headers.setdefault('Origin','https://www.tvnow.de/')

        if self._password_old != "":
            encpassword = encode(self._password_old)
            password = self._password_old
            self._addon.setSetting('password_enc', encpassword)
            self._addon.setSetting('password', "")
            self.sendLogin(self._username, password)

        if self._token != "" and self._username != "":
            self._tokenset = True
            self._session.headers.setdefault('x-auth-token', self._token)
        else:
            self.login()
        
    def _getToken(self, data):
        if (not "pageConfig" in data or not "user" in data["pageConfig"] or
            not "jwt" in data["pageConfig"]["user"]):
            xbmcgui.Dialog().notification(
                'Fehler GetToken', 'Token not found',
                icon=xbmcgui.NOTIFICATION_ERROR)
            return False
        self._token = data["pageConfig"]["user"]["jwt"]
        return True

    def _checkPremium(self):
        base64Parts = self._token.split(".")
        token = "%s==" % base64Parts[1]
        userData = json.loads(base64.b64decode(token))
        if "roles" in userData and "premium" in userData["roles"]:
            self._addon.setSetting('premium', "true")
        elif ("subscriptionState" in userData and
              (userData["subscriptionState"] == 5 or
               userData["subscriptionState"] ==4)):
            self._addon.setSetting('premium', "true")
        if "permissions" in userData:
            if ("vodPremium" in userData["permissions"] and
                userData["permissions"]["vodPremium"] == True):
                self._addon.setSetting('premium', "true")
            if ("livePay" in userData["permissions"] and
                userData["permissions"]["livePay"] == True):
                self._addon.setSetting('livePay', "true")
            if ("liveFree" in userData["permissions"] and
                userData["permissions"]["liveFree"] == True):
                self._addon.setSetting('liveFree', "true")

    def _isLoggedIn(self):
        """Check if User is still logged in with the old Token"""
        if not self._tokenset or self._username == "":
            return False
        loggedIn = True
        base64Parts = self._token.split(".")
        token = "%s==" % base64Parts[1]
        userData = json.loads(base64.b64decode(token))

        if "licenceEndDate" in userData:
            licenceEndDate = userData["licenceEndDate"].split("+")[0]
            try:
                licenceEndDateTS = time.mktime(datetime.datetime.strptime(
                    licenceEndDate, '%Y-%m-%dT%H:%M:%S').timetuple())
                if licenceEndDateTS < (time.time() + 60 * 60 * 24):
                    loggedIn = False
            except:
                loggedIn = False
        else:
            loggedIn = False
        if (loggedIn and "exp" in userData and
            userData["exp"] > (time.time() + 60 * 60 * 24)):
            self._checkPremium()
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
        jlogin = {
            "email" : username,
            "password": password}
        r = self._session.post("https://auth.tvnow.de/login", json=jlogin)
        #Parse json
        response = r.text
        response = json.loads(response)
        statuscode = r.status_code
        if statuscode != 200:
            xbmc.log("Login Error: {}".format(response), level=xbmc.LOGERROR)
            xbmcgui.Dialog().notification(
                'Login Fehler',
                'Login fehlgeschlagen. Bitte Login Daten ueberpruefen',
                 icon=xbmcgui.NOTIFICATION_ERROR)
            return False
        elif "token" in response:
            self._token = response["token"]
            self._tokenset = True
            self._session.headers.setdefault(
                'x-auth-token', response["token"])
            self._usingAccount = True
            self._addon.setSetting('acc_token', self._token)

            self._checkPremium()
            encpassword = encode(password)
            self._addon.setSetting('email', username)
            self._addon.setSetting('password_enc', encpassword)
            return True

    def login(self):
        self._addon.setSetting('premium', "false")
        self._addon.setSetting('livePay', "false")
        self._addon.setSetting('liveFree', "false")
        # If already logged in and active session everything is fine
        if not self._isLoggedIn():
            password = decode(self._addon.getSetting('password_enc'))
            self.usingAccount = False
            if self._username != "" and password != "":
                return self.sendLogin(self._username, password)
        else:
            return True
        # If any case is not matched return login failed
        return False

    def getRecommendationsList(self):
        r = self._session.get("https://bff.apigw.tvnow.de/page/home")
        try:
            os.remove(self._recFile)
        except OSError:
            pass
        if r.status_code == 200:
            with open(self._recFile, "w", encoding='utf-8') as f:
                f.write(r.content.decode())
        try:
            data = r.json()
            if "modules" in data:
                return data["modules"]
        except:
            return []


    def getRecommendation(self, uid):
        data = None
        with open(self._recFile, encoding='utf-8') as json_file:
            data = json.load(json_file)
        if data != None and "modules" in data:
            data = data["modules"]
            for item in data:
                if "id" in item and item["id"] == uid:
                    return item
        return None



    def getPlayBackUrl(self, assetID, loggedIn, live = False, event = False):
        if live:
            if event:
                url = "https://bff.apigw.tvnow.de/player/live/{}".format(
                assetID)
            else:
                url = ("https://bff.apigw.tvnow.de/player/livetv/{}?drm=1&kids=false&playertracking=true") \
                    .format(assetID)
        else:
            url = "https://bff.apigw.tvnow.de/player/{}".format(
                assetID)
        r = self._session.get(url)
        if r.status_code == 402:
            xbmcgui.Dialog().notification(
                'Premiumaccount erforderlich',
                'Dieser Stream ist nur mit Premiumaccount verfuegbar',
                icon=xbmcgui.NOTIFICATION_ERROR)
        elif r.status_code == 403:
            xbmcgui.Dialog().notification(
                'Login erforderlich',
                'Dieser Stream ist nur mit einem Account verfuegbar',
                icon=xbmcgui.NOTIFICATION_ERROR)
        elif r.status_code == 200:
            data = r.json()
            drmProtected = False
            drmURL = ""
            if "videoConfig" in data and "sources" in data["videoConfig"]:
                videoSource = data["videoConfig"]["sources"]
                if "drm" in videoSource:
                    drmProtected = True
                    if "widevine" in videoSource["drm"]:
                        if "url" in videoSource["drm"]["widevine"]:
                            drmURL = videoSource["drm"]["widevine"]["url"]

                if drmProtected and not loggedIn:
                    self._getToken(data)
                if "dashUrl" in videoSource and self._hdEnabled:
                    return videoSource["dashUrl"], drmProtected, drmURL
                # Fallback
                if "dashFallbackUrl" in videoSource:
                    return videoSource["dashFallbackUrl"], drmProtected, drmURL
            if "videoConfig" in data and "videoSource" in data["videoConfig"]:
                videoSource = data["videoConfig"]["videoSource"]
                if "drm" in videoSource:
                    drmProtected = True
                    if "widevine" in videoSource["drm"]:
                        if "url" in videoSource["drm"]["widevine"]:
                            drmURL = videoSource["drm"]["widevine"]["url"]

                if drmProtected and not loggedIn:
                    self._getToken(data)
                if "streams" in videoSource:
                    streams = videoSource["streams"]
                    if "dashHdUrl" in streams and self._hdEnabled:
                        return streams["dashHdUrl"], drmProtected, drmURL
                    # Fallback
                    if "dashUrl" in streams:
                        return streams["dashUrl"], drmProtected, drmURL
            xbmcgui.Dialog().notification(
                    'Abspielen fehlgeschlagen',
                    'Es ist keine AbspielURL vorhanden',
                    icon=xbmcgui.NOTIFICATION_ERROR)
        else:
            xbmcgui.Dialog().notification(
                'Unbekannter Fehler',
                'Für Detail kodi.log prüfen',
                icon=xbmcgui.NOTIFICATION_ERROR)
            xbmc.log("Login Error: {}".format(r.text), level=xbmc.LOGERROR)
        return "", drmProtected, ""


    def play(self, assetID, live=False, event=False):
        loggedIn = self.login()
        # Prepare new ListItem to start playback
        playBackUrl, drmProtected, drmURL = self.getPlayBackUrl(
            assetID, loggedIn, live, event)
        if playBackUrl != "":
            if drmProtected and drmURL == "":
                drmURL = "https://widevine.tvnow.de/index/proxy"
            li = xbmcgui.ListItem()
            protocol = 'mpd'
            drm = 'com.widevine.alpha'
            # Inputstream settings
            if self._helperActivated and drmProtected:
                is_helper = inputstreamhelper.Helper(protocol, drm=drm)
                if is_helper.check_inputstream():
                    is_addon = is_helper.inputstream_addon
            else:
                is_addon = getInputstreamAddon()
                if not is_addon:
                    xbmcgui.Dialog().notification(
                        'TvNow Fehler', 'Inputstream Addon fehlt!',
                         xbmcgui.NOTIFICATION_ERROR, 2000, True)
                    return False
            if drmProtected:
                li.setProperty(is_addon + '.license_type', drm)
                if self._patchManifest:
                    playBackUrl = "http://localhost:42467/?id={}&live={}&event={}" \
                        .format(assetID, 1 if live == True else 0, 1 if event == True else 0)
            li.setProperty(
                is_addon + '.license_key',
                self._licence_url.replace("{LICURL}", drmURL).replace("{TOKEN}", self._token))
            li.setProperty(is_addon + '.manifest_type', protocol)
            if live:
                li.setProperty(
                    is_addon + '.manifest_update_parameter',  "full")
            li.setProperty('inputstream', is_addon)
            li.setPath(playBackUrl)
            # Start Playing
            addon_handle = int(sys.argv[1])
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)

