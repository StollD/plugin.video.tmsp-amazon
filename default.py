import sys
from urllib.parse import parse_qsl, urlparse

from resources.lib.auth import login
from resources.lib.playback import play

query = urlparse(sys.argv[2]).query
args = dict(parse_qsl(query))

if "play" in args:
    play(args["play"])
else:
    login()
