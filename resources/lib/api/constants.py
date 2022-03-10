from typing import *

# This is the app we are impersonating
APP_NAME = "com.amazon.avod.thirdpartyclient"
APP_VERSION = "296016847"
DEVICE_TYPE = "A43PXU4ZN2AL1"

# This is the device we are impersonating
DEVICE_NAME = "mdarcy/nvidia/SHIELD Android TV"
MANUFACTURER = "NVIDIA"
OS_VERSION = (
    "NVIDIA/mdarcy/mdarcy:11/RQ1A.210105.003/7094531_2971.7725:user/release-keys"
)

HEADERS = {
    "Accept-Charset": "utf-8",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SHIELD Android TV RQ1A.210105.003)",
}

# Endpoint for third party devices running Android 9 to 11
AMAZONVIDEO_ENDPOINT = "ab3cs84k69ya"
