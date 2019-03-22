import sys
from tvnow import TvNow
import navigation as nav

tvnow = TvNow()

def playAsset(asset_id):
    #get asset details and build infotag from it
    tvnow.play(asset_id)
    
def playLive(asset_id):
    #get asset details and build infotag from it
    tvnow.play(asset_id, True)
