import time
import json
import urllib2
import requests
from sendung import Sendung
s_a_z_url = "https://api.tvnow.de/v3/formats?fields=id,title,titleGroup,searchAliasName,station,genres,szm.format&filter=%7B%22Station%22%3A%7B%22containsIn%22%3A%5B%22rtl%22%2C%22rtl2%22%2C%22vox%22%2C%22superrtl%22%2C%22nitro%22%2C%22ntv%22%2C%22rtlplus%22%2C%22tvnow%22%5D%7D%7D&order=NameLong%20asc"
class Database():
    def __init__(self):
        self.database = []
        self.sAzDict = {}
        self.catDict = {}
        self.stationDict = {}
        self.lastUpdate = 0
    
    def addToDict(self, d, k, v):
        if not k in d:
            d[k] = []
        d[k].append(v)    

    def updateDatabase(self, force = False):
        if time.time() - self.lastUpdate < 1800 and force == False:
            return False
        print "Building Database"
        self.database = []
        self.sAzDict = {}
        self.catDict = {}
        self.stationDict = {}
        sendungen = []
        response = requests.get(s_a_z_url + "&page=1&maxPerPage=1")
        data = response.json()
        totalitems = data["total"]
        for i in range((totalitems // 250) + 1):
            response = requests.get("%s&page=%d&maxPerPage=250" % (s_a_z_url, i + 1))
            data = response.json()
            for item in data["items"]:
                sendung = Sendung(item["id"], item["title"],item["genres"],item["station"],item["titleGroup"])
                self.database.append(sendung)
                self.addToDict(self.sAzDict,item["titleGroup"],sendung)
                self.addToDict(self.stationDict,item["station"],sendung)
                for cat in item["genres"]:
                    self.addToDict(self.catDict,cat,sendung)
        self.lastUpdate = time.time()
        return True

    def getDict(self, dicttype=""):
        if dicttype == "station":
            return self.stationDict
        elif dicttype == "cat":
            return self.catDict
        else:
            return self.sAzDict