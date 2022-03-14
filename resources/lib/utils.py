import json
import os
import os.path
import uuid
from typing import *

import xbmc
import xbmcaddon
import xbmcvfs

from .api import DEVICE_TYPE_ANDROID, DEVICE_TYPE_BROWSER, AmazonToken


def save_token(token: AmazonToken) -> None:
    addon = xbmcaddon.Addon()

    path = os.path.join(addon.getAddonInfo("profile"), "token.json")
    path = xbmcvfs.translatePath(path)

    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = {
        "access": token.access,
        "refresh": token.refresh,
        "expires": token.expires,
        "cookies": token.cookies,
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

    return AmazonToken(
        data["access"], data["refresh"], data["expires"], data["cookies"]
    )


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


def device_type() -> str:
    if xbmc.getCondVisibility("system.platform.android"):
        return DEVICE_TYPE_ANDROID

    return DEVICE_TYPE_BROWSER


def is_android() -> bool:
    return device_type() == DEVICE_TYPE_ANDROID


def is_browser() -> bool:
    return device_type() == DEVICE_TYPE_BROWSER


def supported_hdr() -> List[str]:
    addon = xbmcaddon.Addon()
    hdr = []

    if addon.getSettingBool("enable_dovi"):
        hdr.append("DolbyVision")

    if addon.getSettingBool("enable_hdr10"):
        hdr.append("Hdr10")

    if len(hdr) == 0:
        hdr.append("None")

    return hdr


def supported_codecs() -> List[str]:
    addon = xbmcaddon.Addon()
    codecs = ["H264"]

    if addon.getSettingInt("enable_h265") == 1:
        codecs.append("H265")

    # NOTE: The following is supported by the API
    #
    #  codecs.append("AV1")
    #
    # But I am not sure if there are any titles
    # with an AV1 stream.

    return codecs


def supported_resolution() -> str:
    addon = xbmcaddon.Addon()

    # Android devices with Widevine L1 can decrypt UHD streams
    # TODO: Check if Android devices with L3 fallback gracefully
    #
    # H265 is required for UHD streams, so if it is disabled,
    # only HD content (up to 1080p) can be requested.
    if is_android():
        if addon.getSettingInt("enable_h265") == 2:
            return "HD"
        else:
            return "UHD"

    # Other platforms (PC) can only get SD streams
    # Higher quality requires VMP verification
    return "SD"


def prefer_atmos() -> str:
    addon = xbmcaddon.Addon()

    # "Prefer Dolby Atmos":
    #       Choose the Atmos track, even if a
    #       track with a higher bitrate exists
    #
    # "Prefer higher bitrate":
    #       Choose the track with the highest bitrate, even
    #       if a Dolby Atmos track with lower bitrate exists.
    return addon.getSettingInt("audio_prefs") == 0
