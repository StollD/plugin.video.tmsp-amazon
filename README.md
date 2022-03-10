# Barebones Amazon Prime Video for Kodi

This is a custom addon for Kodi, to support playback for videos from Amazon Prime Video. The difference between the addon from Sandmann and this one is, that this one supports UHD playback with HDR10 and Dolby Vision.

This is achived by using a slightly more complicated login flow, that allows using the endpoints for the Prime Video Android app. The other addon uses the endpoints for a browser, which are capped at 1080p with no HDR.

The downside is that this addon is absolutely useless, because it has no GUI. To use it, you need to synthesize STRM files with the ASIN of the video you want to play. However, this is not a restriction of the endpoints, it is a restriction of the author (I can't write GUIs, and I dont need them because I synthesize STRM files).

### Example for synthesized STRM file

```bash
# Plays the last episode of The Expanse
# Has UHD and HDR10, but no Dolby Vision
$ cat Expanse-S06E06.strm
plugin://plugin.video.tmsp-amazon/?play=B09PH1V612

# Plays the first episode of Jack Ryan
# One of the few items on Prime Video that has Dolby Vision
$ cat JackRyan-S01E01.strm
plugin://plugin.video.tmsp-amazon/?play=B089Y5SFB1
```

### What doesn't work

* There is no GUI
* Subtitles don't work, need to copy the HTTP proxy from Sandmann
* Dolby Atmos tracks are available from the server, but IS.A ignores them
* There is no sync of watched status or progress


### Requirements

* Kodi 19 or later
* InputStream.Adaptive
* An Amazon Prime Video subscription
* A device with Widevine L1 (like an NVIDIA Shield)
