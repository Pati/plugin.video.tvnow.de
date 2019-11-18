from __future__ import print_function
import time
import json
import requests
from sendung import Sendung
s_a_z_url = "https://apigw.tvnow.de/module/teaserrow/az"
class Database():
    def __init__(self):
        self.database = []
        self.sAzDict = {}
        self.stationDict = {}
        self.lastUpdate = 0
    
    def addToDict(self, d, k, v):
        if not k in d:
            d[k] = []
        d[k].append(v)    

    def updateDatabase(self, force = False):
        if time.time() - self.lastUpdate < 1800 and force == False:
            return False
        print ("Building Database")
        self.database = []
        self.sAzDict = {}
        self.stationDict = {}
        sendungen = []
        response = requests.get(s_a_z_url)
        data = response.json()
        for listItem in data:
            for item in listItem["formats"]:
                sendung = Sendung(item["url"], item["name"],item["station"],item["titleGroup"])
                self.database.append(sendung)
                self.addToDict(self.sAzDict,item["titleGroup"],sendung)
                self.addToDict(self.stationDict,item["station"],sendung)
        self.lastUpdate = time.time()
        return True

    def getDict(self, dicttype=""):
        if dicttype == "station":
            return self.stationDict
        else:
            return self.sAzDict