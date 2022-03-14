import sys
from typing import *
from urllib.parse import urlencode

import requests
import xbmcaddon
import xbmcgui
import xbmcplugin
from inputstreamhelper import Helper

from .api import DEVICE_NAME, HEADERS, AmazonAuth, AmazonURL
from .auth import login
from .utils import *


def base_request(data) -> Dict[str, str]:
    base = {
        "deviceID": device_id(),
        "deviceTypeId": device_type(),
        "format": "json",
        "version": "1",
        "firmware": "1",
    }

    base.update(data)
    return base


def playback_request(data) -> Dict[str, str]:
    base = {
        "audioTrackId": "all",
        "consumptionType": "Streaming",
        "deviceBitrateAdaptationsOverride": "CVBR,CBR",
        "deviceDrmOverride": "CENC",
        "deviceHdrFormatsOverride": ",".join(supported_hdr()),
        "deviceProtocolOverride": "Https",
        "deviceStreamingTechnologyOverride": "DASH",
        "deviceVideoCodecOverride": ",".join(supported_codecs()),
        "deviceVideoQualityOverride": supported_resolution(),
        "languageFeature": "MLFv2",
        "resourceUsage": "ImmediateConsumption",
        "subtitleFormat": "TTMLv2",
        "supportedDRMKeyScheme": "DUAL_KEY",
    }

    base.update(data)
    return base_request(base)


def get_endpoint() -> AmazonURL:
    url = AmazonURL("amazon.com")

    data = base_request({})
    resp = requests.get(url.config() + "?" + urlencode(data), headers=HEADERS)
    if resp.status_code != 200:
        raise Exception("Failed to get region config")

    data = resp.json()

    host = data["territoryConfig"]["defaultVideoWebsite"]
    host = host.lstrip("https://")
    host = host.lstrip("www.")

    region = data["customerConfig"]["homeRegion"].lower()
    region = "" if "na" in region else "-" + region

    api = "atv-ps{}.{}".format(region, host)
    marketplace = data["customerConfig"]["marketplaceId"]

    return AmazonURL(host, api), marketplace


def play(asin: str) -> None:
    # If no token can be loaded, start the login process
    token = load_token()
    if token is None:
        token = login()

    # Check if IS.A is available
    ish = Helper("mpd", drm="com.widevine.alpha")
    if not ish.check_inputstream():
        raise Exception("Inputstream.Adaptive not active")

    url, marketplace = get_endpoint()
    auth = AmazonAuth(token, url, is_browser(), save_token)

    session = requests.Session()
    session.auth = auth
    session.headers.update(HEADERS)

    # Grab the MPD from Amazon
    data = playback_request(
        {
            "asin": asin,
            "marketplaceID": marketplace,
            "desiredResources": "PlaybackUrls,SubtitleUrls,ForcedNarratives,TransitionTimecodes",
            "videoMaterialType": "Feature",
        }
    )

    resp = session.get(url.playback() + "?" + urlencode(data))
    if resp.status_code != 200:
        raise Exception("Failed to get playback resources")

    data = resp.json()

    # Handle errors
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
    tech = host["urls"]["manifest"]["streamingTechnology"]
    drm = host["urls"]["manifest"]["drm"]

    if drm != "CENC" or tech != "DASH":
        raise Exception("Only MPEG-DASH with Widevine is supported")

    ##
    # TODO: Support subtitles
    ##

    # Prepare the widevine license URL
    data = playback_request(
        {
            "asin": asin,
            "marketplaceID": marketplace,
            "desiredResources": "Widevine2License",
            "videoMaterialType": "Feature",
        }
    )

    lic = url.playback() + "?" + urlencode(data)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    headers.update(HEADERS)
    headers.update(session.auth.get_headers())

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
