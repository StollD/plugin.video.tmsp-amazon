from base64 import urlsafe_b64decode
from typing import *

import json
import requests
from bottle import Bottle, abort, request, response

from .api import HEADERS
from .mpd import patch_mpd

HOST = "localhost"
PORT = 26473

app = Bottle()


def urlb64(i: str) -> str:
    return urlsafe_b64decode(i).decode()


@app.get("/mpd")
def mpd() -> str:
    url = urlb64(request.query.get("url"))
    subs = json.loads(urlb64(request.query.get("subs")))
    forced = json.loads(urlb64(request.query.get("forced")))

    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        abort(resp.status_code, resp.text)

    response.content_type = "application/xml+dash"
    return patch_mpd(url, resp.text, subs, forced)


def start_proxy() -> None:
    app.run(host="localhost", port=26473)


def stop_proxy() -> None:
    app.close()
