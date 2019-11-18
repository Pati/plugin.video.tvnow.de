try:
    import urllib.parse as ul
except:
    import urllib as ul
import xbmcaddon

base_url = "plugin://" + xbmcaddon.Addon().getAddonInfo('id')


def build_url(query):
    return base_url + '?' + ul.urlencode(query)