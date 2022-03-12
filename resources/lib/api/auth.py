from datetime import datetime, timedelta
from typing import *

import requests
import requests.auth

from .constants import *
from .token import AmazonToken
from .url import AmazonURL


class AmazonAuth(requests.auth.AuthBase):
    token: AmazonToken
    url: AmazonURL
    use_cookies: bool
    on_save: Callable[[AmazonToken], None]

    def __init__(
        self,
        token: AmazonToken,
        url: AmazonURL,
        use_cookies: bool,
        on_save: Callable[[AmazonToken], None],
    ):
        self.token = token
        self.url = url
        self.use_cookies = use_cookies
        self.on_save = on_save

    def refresh_oauth(self) -> None:
        if not self.token.oauth_expired():
            return

        req = {
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "source_token": self.token.refresh,
            "source_token_type": "refresh_token",
            "requested_token_type": "access_token",
        }

        resp = requests.post(self.url.token(), headers=HEADERS, json=req)
        if resp.status_code != 200:
            raise Exception("Token refresh failed")

        data = resp.json()
        expires_in = int(data["expires_in"])

        self.token.access = data["access_token"]
        self.token.expires = (
            datetime.utcnow() + timedelta(seconds=expires_in)
        ).timestamp()
        self.on_save(self.token)

    def refresh_cookies(self) -> None:
        if not self.token.cookies_expired():
            return

        req = {
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "source_token": self.token.refresh,
            "source_token_type": "refresh_token",
            "requested_token_type": "auth_cookies",
            "domain": "." + self.url.domain,
        }

        resp = requests.post(self.url.cookies(), headers=HEADERS, data=req)
        if resp.status_code != 200:
            raise Exception("Cookie refresh failes")

        data = resp.json()

        cookies = {}
        for c in data["response"]["tokens"]["cookies"][req["domain"]]:
            time = dateutil.parser.parse(c["Expires"])
            time = datetime.utcfromtimestamp(time.timestamp())

            cookies[c["Name"]] = {
                "value": c["Value"],
                "expires": time.timestamp(),
            }

        self.token.cookies = cookies
        self.on_save(self.token)

    def get_headers(self) -> Dict[str, str]:
        if self.token is None:
            return {}

        if self.token.access is not None and not self.use_cookies:
            self.refresh_oauth()

            return {"Authorization": "Bearer " + self.token.access}

        if self.token.cookies is not None and self.use_cookies:
            self.refresh_cookies()

            cookies = []
            for c in self.token.cookies:
                cookies.append(c + "=" + self.token.cookies[c]["value"])

            return {"Cookie": ";".join(cookies)}

        return {}

    def __call__(self, request):
        request.headers.update(self.get_headers())
        return request
