from datetime import datetime, timedelta

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

    def get_headers(self) -> Dict[str, str]:
        if self.token is None:
            return {}

        if self.token.access is not None and not self.use_cookies:
            self.refresh()

            return {"Authorization": "Bearer " + self.token.access}

        if self.token.cookies is not None and self.use_cookies:
            cookies = []
            for c in self.token.cookies:
                cookies.append(c + "=" + self.token.cookies[c])

            return {"Cookie": ";".join(cookies)}

        return {}

    def __call__(self, request):
        request.headers.update(self.get_headers())
        return request
