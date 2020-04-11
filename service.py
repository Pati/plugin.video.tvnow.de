# -*- coding: utf-8 -*-
# Created on: 21.10.2019
"""Kodi plugin for Tvnow (https://tvnow.de)"""

import sys
import threading
import traceback
import xbmc

import resources.lib.manifestServer as manifestServer


class TvNowService(object):
    """
    TvNowService addon service
    """

    def __init__(self):
        self.server = {
            'class': manifestServer.ManifestServer,
            'instance': None,
            'thread': None}
        self.init_server()

    def init_server(self):
        self.server['class'].allow_reuse_address = True
        self.server['instance'] = self.server['class'](
            ('127.0.0.1', 42467))
        self.server['thread'] = threading.Thread(
            target=self.server['instance'].serve_forever)

    def start_services(self):
        """
        Start the background services
        """
        self.server['instance'].server_activate()
        self.server['instance'].timeout = 1
        self.server['thread'].start()

    def shutdown(self):
        """
        Stop the background services
        """
        self.server['instance'].server_close()
        self.server['instance'].shutdown()
        self.server['instance'] = None
        self.server['thread'].join()
        self.server['thread'] = None

    def run(self):
        """Main loop. Runs until xbmc.Monitor requests abort"""
        try:
            self.start_services()
        except Exception as exc:
            return
        monitor = xbmc.Monitor()

        while not monitor.abortRequested():
            monitor.waitForAbort(1)
        self.shutdown()


if __name__ == '__main__':
    TvNowService().run()
