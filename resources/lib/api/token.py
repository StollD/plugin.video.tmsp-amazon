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

    def expired(self) -> bool:
        return datetime.fromtimestamp(self.expires) <= datetime.utcnow()
