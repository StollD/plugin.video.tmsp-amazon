import copy
import posixpath
from typing import *
from xml.etree import ElementTree

import requests

from .api import HEADERS
from .utils import *

NAMESPACES = {
    "cenc": "urn:mpeg:cenc:2013",
    "dash": "urn:mpeg:dash:schema:mpd:2011",
}


def find(tree: ElementTree.Element, xpath: str) -> List[ElementTree.Element]:
    return tree.find(xpath, namespaces=NAMESPACES)


def findall(tree: ElementTree.Element, xpath: str) -> List[ElementTree.Element]:
    return tree.findall(xpath, namespaces=NAMESPACES)


def patch_full_url(tree: ElementTree.Element, url: str) -> None:
    base_url = posixpath.dirname(url)

    for elem in findall(tree, ".//dash:BaseURL"):
        elem.text = base_url + "/" + elem.text

    for elem in findall(tree, ".//dash:SegmentTemplate[@media]"):
        elem.set("media", base_url + "/" + elem.get("media"))

    for elem in findall(tree, ".//dash:SegmentTemplate[@initialization]"):
        elem.set("initialization", base_url + "/" + elem.get("initialization"))


def split_adaptation_sets(tree: ElementTree.Element) -> None:
    adsets = findall(tree, "./dash:AdaptationSet")

    for adset in adsets:
        if adset.get("contentType") != "audio":
            continue

        reps = findall(adset, "./dash:Representation")

        # Create a copy of the adaptation set for every representation
        for i in range(0, len(reps)):
            cp_adset = copy.deepcopy(adset)
            cp_reps = findall(cp_adset, "./dash:Representation")

            for j in range(0, len(reps)):
                if i == j:
                    continue

                cp_adset.remove(cp_reps[j])

            if "minBandwidth" in cp_adset.attrib:
                del cp_adset.attrib["minBandwidth"]

            if "maxBandwidth" in cp_adset.attrib:
                del cp_adset.attrib["maxBandwidth"]

            # Add the new adaptation set...
            tree.append(cp_adset)

        # and remove the old one once all its
        # representations have been cloned
        tree.remove(adset)


# Is A a better audio track than B?
def is_higher_quality(a: ElementTree.Element, b: ElementTree.Element) -> bool:
    atmos_a = len(findall(a, ".//dash:SupplementalProperty[@value='JOC']")) > 0
    atmos_b = len(findall(b, ".//dash:SupplementalProperty[@value='JOC']")) > 0

    if atmos_a != atmos_b and prefer_atmos():
        return atmos_a

    bitrate_a = int(find(a, "./dash:Representation").get("bandwidth"))
    bitrate_b = int(find(b, "./dash:Representation").get("bandwidth"))

    return bitrate_a > bitrate_b


def patch_audio_metadata(tree: ElementTree.Element) -> None:
    adsets = findall(tree, "./dash:AdaptationSet")

    found = {}

    for adset in adsets:
        if adset.get("contentType") != "audio":
            continue

        track_id = adset.get("audioTrackId")

        # This is the first track we found for that track id
        if track_id not in found:
            adset.set("default", "true")
            found[track_id] = adset

        # We already found a track for this id, but this track is better
        elif is_higher_quality(adset, found[track_id]):
            adset.set("default", "true")
            found[track_id].set("default", "false")
            found[track_id] = adset

        # This track is not better than what we already found
        else:
            adset.set("default", "false")

        # Remove the Role tag, because it overrides the default value
        adset.remove(find(adset, "./dash:Role"))

        # Set flag for audio descriptions
        if "descriptive" in track_id:
            adset.set("impaired", "true")
        else:
            adset.set("impaired", "false")

        # Use the name property to show the bitrate in Kodi
        bitrate = int(find(adset, "./dash:Representation").get("bandwidth"))
        adset.set("name", "{:3d} kbps".format(bitrate // 1000))


def patch_mpd(url: str, manifest: str) -> str:
    for namespace in NAMESPACES:
        ElementTree.register_namespace(namespace, NAMESPACES[namespace])

    tree = ElementTree.fromstring(manifest)

    for parent in findall(tree, "./*[dash:AdaptationSet]"):
        # Replace relative URLs with absolute ones. Required because of the proxy
        patch_full_url(parent, url)

        # Split up adaptation sets with multiple representations, so that IS.A exposes
        # all available streams to Kodi. Otherwise it will just choose the first one.
        split_adaptation_sets(parent)

        # Patch audio metadata, to set default streams
        patch_audio_metadata(parent)

    txt = ElementTree.tostring(manifest, encoding="unicode")

    # The dash: namespace confuses IS.A, so patch it out
    txt = txt.replace("xmlns:dash", "xmlns")
    txt = txt.replace("<dash:", "<")
    txt = txt.replace("</dash:", "</")

    return txt
