try:
    import urllib.parse as ul
except:
    import urllib as ul
import xbmcaddon
import xbmc
import xbmcgui
import uuid
import json
import base64

try:  # Python 3
    from Crypto.Cipher import DES3
    from Crypto.Util.Padding import pad, unpad
except:
    from Cryptodome.Cipher import DES3
    from Cryptodome.Util.Padding import pad, unpad

from platform import node

base_url = "plugin://" + xbmcaddon.Addon().getAddonInfo('id')


def build_url(query):
    return base_url + '?' + ul.urlencode(query)


# Get installed inputstream addon
def getInputstreamAddon():
    is_types = ['inputstream.adaptive', 'inputstream.smoothstream']
    for i in is_types:
        r = xbmc.executeJSONRPC(
            '{"jsonrpc": "2.0", "id": 1, "method": "Addons.GetAddonDetails", '
            + '"params": {"addonid":"' + i + '", "properties": ["enabled"]}}')
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
    k = DES3.new(
        getmac(), DES3.MODE_CBC, iv="\0\0\0\0\0\0\0\0".encode("utf8"))
    d = k.encrypt(pad(data.encode("utf8"),8))
    return base64.b64encode(d)

def decode(data):
    if not data:
        return ''
    k = DES3.new(
        getmac(), DES3.MODE_CBC, iv="\0\0\0\0\0\0\0\0".encode("utf8"))
    try:
        d = unpad(k.decrypt(base64.b64decode(data)), 8).decode("utf8")
        return d
    except:
        xbmcgui.Dialog().notification(
            'Login Fehler',
            'Login fehlgeschlagen. Bitte Login Daten ueberpruefen',
            icon=xbmcgui.NOTIFICATION_ERROR)
        addon = xbmcaddon.Addon()
        addon.setSetting('password_enc', "")
        addon.setSetting('email', "")
        return ""

def parseDateTime(str):
    try:
        m = re.search(
            r'[A-z]+\.\s+([0-9]+).([0-9]+).([0-9]+),\s+([0-9]+):([0-9]+)',
            str)
        if m:
            return datetime.datetime(
                int(m.group(3)),int(m.group(2)), int(m.group(1)),
                int(m.group(4)), int(m.group(5)))
    except:
        return None