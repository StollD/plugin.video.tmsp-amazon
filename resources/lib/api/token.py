from datetime import datetime, timedelta
from typing import *


class AmazonToken:
    access: str
    refresh: str
    expires: float
    cookies: Dict[str, str]

    def __init__(
        self,
        access: str,
        refresh: str,
        expires: float,
        cookies: Dict[str, str],
    ):
        self.access = access
        self.refresh = refresh
        self.expires = expires
        self.cookies = cookies

    def oauth_expired(self) -> bool:
        return datetime.fromtimestamp(self.expires) <= datetime.utcnow()

    def cookies_expired(self) -> bool:
        for c in self.cookies:
            date = datetime.fromtimestamp(self.cookies[c]["expires"])

            if date <= datetime.utcnow():
                return True

        return False
