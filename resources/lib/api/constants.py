from typing import *

# TODO: Check if the impersonation is needed?
#       We shouldn't lie if we dont have to.

# This is the app we are impersonating
APP_NAME = "com.amazon.avod.thirdpartyclient"
APP_VERSION = "296016847"

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

DEVICE_TYPE_ANDROID = "A43PXU4ZN2AL1"
DEVICE_TYPE_BROWSER = "AOAGZA014O5RE"
