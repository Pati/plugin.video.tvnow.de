from resources.lib.tvnow import TvNow

tvnow = TvNow()

def playAsset(asset_id):
    #get asset details and build infotag from it
    tvnow.play(asset_id)
    
def playLive(asset_id):
    #get asset details and build infotag from it
    tvnow.play(asset_id, True)
