import base64
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import *
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from bs4 import BeautifulSoup

from .constants import *
from .token import AmazonToken
from .url import AmazonURL


class AmazonLogin:
    url: AmazonURL
    username: str
    password: str
    serial: str
    callback_2fa: Callable[[], str]
    session: requests.Session

    def __init__(
        self,
        url: AmazonURL,
        username: str,
        password: str,
        serial: str,
        callback_2fa: Callable[[], str],
    ):
        self.url = url
        self.username = username
        self.password = password
        self.serial = serial
        self.callback_2fa = callback_2fa

        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def create_code_verifier(self) -> bytes:
        verifier = secrets.token_bytes(32)
        return base64.urlsafe_b64encode(verifier).rstrip(b"=")

    def create_code_challenge(self, verifier: bytes) -> bytes:
        h = hashlib.sha256(verifier)
        return base64.urlsafe_b64encode(h.digest()).rstrip(b"=")

    def client_id(self) -> str:
        return (self.serial.encode() + b"#" + DEVICE_TYPE_ANDROID.encode()).hex()

    def build_oauth(self) -> Tuple[str, bytes]:
        verifier = self.create_code_verifier()
        challenge = self.create_code_challenge(verifier)

        params = {
            "openid.oa2.response_type": "code",
            "openid.oa2.code_challenge_method": "S256",
            "openid.oa2.code_challenge": challenge.decode(),
            "openid.return_to": self.url.landing(),
            "openid.assoc_handle": "amzn_piv_android_v2_de",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "pageId": "amzn_device_common_dark",
            "accountStatusPolicy": "P1",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.mode": "checkid_setup",
            "openid.ns.oa2": "http://www.amazon.com/ap/ext/oauth/2",
            "openid.oa2.client_id": "device:{}".format(self.client_id()),
            "openid.ns.pape": "http://specs.openid.net/extensions/pape/1.0",
            "openid.oa2.scope": "device_auth_access",
            "forceMobileLayout": "true",
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.pape.max_auth_age": "0",
        }

        return self.url.signin() + "?" + urlencode(params), verifier

    def get_form_inputs(self, form) -> Dict:
        data = {}

        for field in form.find_all("input"):
            try:
                data[field["name"]] = ""
                if field["type"] and field["type"] == "hidden":
                    data[field["name"]] = field["value"]
            except:
                pass

        return data

    def login(self) -> AmazonToken:
        url, verifier = self.build_oauth()

        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        form = soup.find("form", {"name": "signIn"})
        data = self.get_form_inputs(form)

        data["email"] = self.username
        data["password"] = self.password

        method = form.get("method", "GET")
        action = form["action"]

        resp = self.session.request(method, action, data=data)
        soup = BeautifulSoup(resp.text, "html.parser")

        while self.check_2fa(soup):
            form = soup.find("form")
            data = self.get_form_inputs(form)

            data["otpCode"] = self.callback_2fa()
            data["mfaSubmit"] = "Submit"
            data["rememberDevice"] = "false"

            method = form.get("method", "GET")
            action = form["action"]

            resp = self.session.request(method, action, data=data)
            soup = BeautifulSoup(resp.text, "html.parser")

        self.session.close()
        parsed_url = parse_qs(urlparse(resp.url).query)

        if "openid.oa2.authorization_code" not in parsed_url:
            raise Exception("Login failed.")

        auth_code = parsed_url["openid.oa2.authorization_code"][0]

        return self.register(verifier, auth_code)

    def check_2fa(self, soup: BeautifulSoup) -> bool:
        if soup.find("form", id=lambda x: x and "auth-mfa-form" in x):
            return True

        return False

    def register(self, verifier: bytes, auth_code: str) -> AmazonToken:
        data = {
            "auth_data": {
                "client_id": self.client_id(),
                "authorization_code": auth_code,
                "code_verifier": verifier.decode(),
                "code_algorithm": "SHA-256",
                "client_domain": "DeviceLegacy",
            },
            "registration_data": {
                "domain": "DeviceLegacy",
                "device_type": DEVICE_TYPE_ANDROID,
                "device_serial": self.serial,
                "app_name": APP_NAME,
                "app_version": APP_VERSION,
                "device_model": DEVICE_NAME,
                "os_version": OS_VERSION,
            },
            "requested_token_type": [
                "bearer",
                "website_cookies",
            ],
            "requested_extensions": [
                "device_info",
                "customer_info",
            ],
            "cookies": {
                "domain": "." + self.url.domain,
                "website_cookies": [],
            },
        }

        resp = requests.post(self.url.register(), headers=HEADERS, json=data)

        if resp.status_code != 200:
            raise Exception("Device registration failed.")

        data = resp.json()["response"]["success"]

        access = data["tokens"]["bearer"]["access_token"]
        refresh = data["tokens"]["bearer"]["refresh_token"]

        expires_in = int(data["tokens"]["bearer"]["expires_in"])
        expires = (datetime.utcnow() + timedelta(seconds=expires_in)).timestamp()

        cookies = {}
        for c in data["tokens"]["website_cookies"]:
            cookies[c["Name"]] = c["Value"]

        return AmazonToken(access, refresh, expires, cookies)
