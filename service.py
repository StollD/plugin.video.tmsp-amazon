import xbmc
import threading

from resources.lib.proxy import start_proxy, stop_proxy

thread = threading.Thread(target=start_proxy)
thread.start()

monitor = xbmc.Monitor()
monitor.waitForAbort()

stop_proxy()
thread.join()
