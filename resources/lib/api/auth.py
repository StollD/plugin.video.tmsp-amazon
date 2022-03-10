from datetime import datetime, timedelta

import requests
import requests.auth

from .constants import *
from .token import AmazonToken
from .url import AmazonURL


class AmazonAuth(requests.auth.AuthBase):
    token: AmazonToken
    url: AmazonURL
    on_save: Callable[[AmazonToken], None]

    def __init__(
        self, token: AmazonToken, url: AmazonURL, on_save: Callable[[AmazonToken], None]
    ):
        self.token = token
        self.url = url
        self.on_save = on_save

    def refresh(self) -> None:
        if self.token is None:
            return

        if not self.token.expired():
            return

        if self.token.refresh is None:
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

    def __call__(self, request):
        self.refresh()

        if not (self.token.access is None):
            request.headers["Authorization"] = "Bearer {}".format(self.token.access)

        return request
