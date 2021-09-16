from __future__ import print_function
import time
import json
import requests
from resources.lib.sendung import Sendung
s_a_z_url = "https://bff.apigw.tvnow.de/module/teaserrow/az"
class Database():
    def __init__(self):
        self._database = []
        self._sAzDict = {}
        self._stationDict = {}
        self._lastUpdate = 0
        self._version = 1

    def _addToDict(self, d, k, v):
        if not k in d:
            d[k] = []
        d[k].append(v)

    def updateDatabase(self, force = False):
        if time.time() - self._lastUpdate < 1800 and force == False and self._version >= 2:
            return False
        self._database = []
        self._sAzDict = {}
        self._stationDict = {}
        self._version = 2
        response = requests.get(s_a_z_url)
        data = response.json()
        for listItem in data:
            for item in listItem["formats"]:
                sendung = Sendung(
                    item["url"], item["name"], item["station"],
                    item["titleGroup"], item["type"])
                self._database.append(sendung)
                self._addToDict(self._sAzDict,item["titleGroup"],sendung)
                self._addToDict(self._stationDict,item["station"],sendung)
        self.lastUpdate = time.time()
        return True

    def getDict(self, dicttype=""):
        if dicttype == "station":
            return self._stationDict
        else:
            return self._sAzDict