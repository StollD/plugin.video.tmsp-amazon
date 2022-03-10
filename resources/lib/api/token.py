from datetime import datetime, timedelta
from typing import *


class AmazonToken:
    access: str
    refresh: str
    expires: float

    def __init__(self, access: str, refresh: str, expires: float):
        self.access = access
        self.refresh = refresh
        self.expires = expires

    def expired(self) -> bool:
        return datetime.fromtimestamp(self.expires) <= datetime.utcnow()
