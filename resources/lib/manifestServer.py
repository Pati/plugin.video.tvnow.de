try:
    import BaseHTTPServer
except:
    import http.server as BaseHTTPServer
import requests
try:
    from SocketServer import TCPServer
except:
    from socketserver import TCPServer
try:
    from urlparse import urlparse, parse_qs
except:
    from urllib.parse import urlparse, parse_qs
import tvnow
import re

class ManifestServerHttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Removes pssh Data from Manifests"""

    def do_HEAD(self):
        """Answers head requests with a success code"""
        self.send_response(200)

    def do_GET(self):
        """Loads the XML manifest for the requested resource"""
        try:
            params = parse_qs(urlparse(self.path).query)
            TvNow = tvnow.TvNow()
            if TvNow.login(True):
                playBackUrl, drmProtected = TvNow.getPlayBackUrl(int(params['id'][0]),int(params['live'][0]) == 1)
                if playBackUrl != "":
                    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0"}
                    r = requests.get(playBackUrl,headers=headers)
                    data = r.text
                    data = re.sub(r'<ContentProtection[^>]*>\s*<(cenc:)?pssh[^>]*>[^>]*</(cenc:)?pssh>\s*</ContentProtection>', '', data)
                    basePath = "/".join(playBackUrl.split('/')[:-1])
                    data = re.sub(r'<BaseURL>([^>]*)</BaseURL>', '<BaseURL>'+basePath+r'/\1</BaseURL>', data)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/xml')
                    self.end_headers()
                    try:
                        data = data.encode()
                    except:
                        pass
                    self.wfile.write(data)
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
            else:
                self.send_response(403)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
        except Exception as exc:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(str(exc))
            

    def log_message(self, *args):
        """Disable the BaseHTTPServer Log"""
        pass


class ManifestServer(TCPServer):
    """Override TCPServer to allow usage of shared members"""
    def __init__(self, server_address):
        """Initialization of ManifestServer"""
        TCPServer.__init__(self, server_address, ManifestServerHttpRequestHandler)
