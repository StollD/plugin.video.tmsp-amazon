import sys
from typing import *
from urllib.parse import urlencode

import requests
import xbmcaddon
import xbmcgui
import xbmcplugin
from inputstreamhelper import Helper

from .api import DEVICE_NAME, DEVICE_TYPE, HEADERS, AmazonAuth, AmazonURL
from .auth import login
from .utils import *


def play(asin: str) -> None:
    # If no token can be loaded, start the login process
    token = load_token()
    if token is None:
        token = login()

    ish = Helper("mpd", drm="com.widevine.alpha")
    if not ish.check_inputstream():
        raise Exception("Inputstream.Adaptive not active")

    url = AmazonURL("amazon.com")

    # Query Amazon for the marketplace of our device
    data = {
        "deviceID": device_id(),
        "deviceTypeId": DEVICE_TYPE,
        "format": "json",
        "version": "1",
        "firmware": "1",
    }

    query = urlencode(data)
    resp = requests.get(url.config() + "?" + query, headers=HEADERS)
    if resp.status_code != 200:
        raise Exception("Failed to get region config")

    data = resp.json()

    host = data["territoryConfig"]["defaultVideoWebsite"]
    host = host.lstrip("https://www.")

    api = data["customerConfig"]["baseUrl"]
    marketplace = data["customerConfig"]["marketplaceId"]

    url = AmazonURL(host, api)
    auth = AmazonAuth(token, url, save_token)

    session = requests.Session()
    session.auth = auth
    session.headers.update(HEADERS)

    addon = xbmcaddon.Addon()
    hdr_formats = []

    if addon.getSettingBool("enable_dovi"):
        hdr_formats.append("DolbyVision")

    if addon.getSettingBool("enable_hdr10"):
        hdr_formats.append("Hdr10")

    if len(hdr_formats) == 0:
        hdr_formats.append("None")

    # Grab the MPD from Amazon
    data = {
        "asin": asin,
        "deviceID": device_id(),
        "deviceTypeId": DEVICE_TYPE,
        "marketplaceID": marketplace,
        "format": "json",
        "version": "1",
        "firmware": "1",
        "audioTrackId": "all",
        "consumptionType": "Streaming",
        "videoMaterialType": "Feature",
        "desiredResources": "PlaybackUrls,SubtitleUrls,ForcedNarratives,TransitionTimecodes",
        "subtitleFormat": "TTMLv2",
        "deviceDrmOverride": "CENC",
        "languageFeature": "MLFv2",
        "deviceProtocolOverride": "Https",
        "deviceHdrFormatsOverride": ",".join(hdr_formats),
        "deviceVideoQualityOverride": "UHD",
        "supportedDRMKeyScheme": "DUAL_KEY",
        "resourceUsage": "ImmediateConsumption",
        "deviceBitrateAdaptationsOverride": "CVBR,CBR",
        "deviceStreamingTechnologyOverride": "DASH",
    }

    resp = session.get(url.playback() + "?" + urlencode(data))
    if resp.status_code != 200:
        raise Exception("Failed to get MPD")

    data = resp.json()

    if "error" in data:
        err = data["error"]
    elif "PlaybackUrls" in data.get("errorsByResource", ""):
        err = data["errorsByResource"]["PlaybackUrls"]
    else:
        err = None

    if err is not None:
        raise Exception("{}: {}".format(err["errorCode"], err["message"]))

    sets = data["playbackUrls"]["urlSets"]
    host = sets[data["playbackUrls"]["defaultUrlSetId"]]

    manifest = host["urls"]["manifest"]["url"]

    if not manifest.endswith(".mpd"):
        raise Exception("Only MPEG-DASH manifests are supported")

    ##
    # TODO: Support subtitles
    ##

    # Prepare the widevine license URL
    data = {
        "asin": asin,
        "deviceID": device_id(),
        "deviceTypeId": DEVICE_TYPE,
        "marketplaceID": marketplace,
        "format": "json",
        "version": "1",
        "firmware": "1",
        "audioTrackId": "all",
        "consumptionType": "Streaming",
        "videoMaterialType": "Feature",
        "desiredResources": "Widevine2License",
        "subtitleFormat": "TTMLv2",
        "deviceDrmOverride": "CENC",
        "languageFeature": "MLFv2",
        "deviceProtocolOverride": "Https",
        "deviceHdrFormatsOverride": ",".join(hdr_formats),
        "deviceVideoQualityOverride": "UHD",
        "supportedDRMKeyScheme": "DUAL_KEY",
        "resourceUsage": "ImmediateConsumption",
        "deviceBitrateAdaptationsOverride": "CVBR,CBR",
        "deviceStreamingTechnologyOverride": "DASH",
    }

    lic = url.playback() + "?" + urlencode(data)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Bearer " + auth.token.access,
    }

    headers.update(HEADERS)

    lic += "|" + urlencode(headers)
    lic += "|widevine2Challenge=B{SSM}&includeHdcpTestKeyInLicense=true"
    lic += "|JBlicense;hdcpEnforcementResolutionPixels"

    item = xbmcgui.ListItem(path=manifest)
    item.setMimeType("application/xml+dash")
    item.setContentLookup(False)

    item.setProperty("inputstream", "inputstream.adaptive")
    item.setProperty("inputstream.adaptive.manifest_type", "mpd")
    item.setProperty("inputstream.adaptive.license_type", "com.widevine.alpha")
    item.setProperty("inputstream.adaptive.license_key", lic)
    item.setProperty("inputstream.adaptive.stream_headers", urlencode(HEADERS))

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=item)
