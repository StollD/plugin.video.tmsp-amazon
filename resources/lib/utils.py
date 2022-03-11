import json
import os
import os.path
import uuid
from typing import *

import xbmc
import xbmcaddon
import xbmcvfs

from .api import AmazonToken


def save_token(token: AmazonToken) -> None:
    addon = xbmcaddon.Addon()

    path = os.path.join(addon.getAddonInfo("profile"), "token.json")
    path = xbmcvfs.translatePath(path)

    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = {
        "access": token.access,
        "refresh": token.refresh,
        "expires": token.expires,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_token() -> AmazonToken:
    addon = xbmcaddon.Addon()

    path = os.path.join(addon.getAddonInfo("profile"), "token.json")
    path = xbmcvfs.translatePath(path)

    os.makedirs(os.path.dirname(path), exist_ok=True)

    if not os.path.exists(path):
        return None

    with open(path) as f:
        data = json.load(f)
        return AmazonToken(data["access"], data["refresh"], data["expires"])


def clear_token() -> None:
    addon = xbmcaddon.Addon()

    path = os.path.join(addon.getAddonInfo("profile"), "token.json")
    path = xbmcvfs.translatePath(path)

    if not os.path.exists(path):
        return

    os.remove(path)


def device_id() -> str:
    addon = xbmcaddon.Addon()

    path = os.path.join(addon.getAddonInfo("profile"), "deviceID.txt")
    path = xbmcvfs.translatePath(path)

    os.makedirs(os.path.dirname(path), exist_ok=True)

    if not os.path.exists(path):
        serial = uuid.uuid4().hex

        with open(path, "w", encoding="utf-8") as f:
            f.write(serial)
    else:
        with open(path) as f:
            serial = f.read()

    return serial


def supported_resolution() -> str:
    # Android devices with Widevine L1 can decrypt UHD streams
    # TODO: Check if Android devices with L3 fallback gracefully
    if xbmc.getCondVisibility("system.platform.android"):
        return "UHD"

    # Other platforms (PC) can only get SD streams
    # Higher quality requires VMP verification
    return "SD"
