import os
import os.path
import uuid
from urllib.parse import urlparse

import requests
import xbmcgui

from .api import HEADERS, AmazonLogin, AmazonToken, AmazonURL
from .utils import *


def handle_2fa() -> str:
    dialog = xbmcgui.Dialog()

    otp = dialog.input("Please enter the 2FA Code")
    if otp is None or len(otp) == 0:
        raise Exception("Invalid OTP")

    return otp


def login() -> AmazonToken:
    dialog = xbmcgui.Dialog()

    token = load_token()
    if token is not None:
        ret = dialog.yesno("Prime Video", "You are already logged in. Log out?")
        if ret == 1:
            clear_token()

        return None

    red = requests.get("https://primevideo.com/auth-redirect", headers=HEADERS).url
    region = urlparse(red).netloc.lstrip("www.")

    # Get username
    username = dialog.input("Please enter your username")
    if username is None or len(username) == 0:
        raise Exception("Invalid username")

    # Get password
    password = dialog.input("Please enter your password")
    if password is None or len(password) == 0:
        raise Exception("Invalid password")

    url = AmazonURL(region)
    amazon = AmazonLogin(url, username, password, device_id(), handle_2fa)

    token = amazon.login()
    save_token(token)

    dialog.ok("Success!", "You are now logged in.")
    return token
