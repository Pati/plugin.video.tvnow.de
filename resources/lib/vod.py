from resources.lib.tvnow import TvNow

tvnow = TvNow()

def playAsset(asset_id):
    tvnow.play(asset_id)

def playLive(asset_id):
    tvnow.play(asset_id, True)

def playEvent(asset_id):
    tvnow.play(asset_id, True, True)
