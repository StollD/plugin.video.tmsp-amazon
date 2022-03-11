from typing import *


class AmazonURL:
    domain: str
    api: str

    def __init__(self, domain: str, api: str = None):
        self.domain = domain
        self.api = api

    def token(self) -> str:
        return "https://api.{}/auth/token".format(self.domain)

    def signin(self) -> str:
        return "https://www.{}/ap/signin".format(self.domain)

    def landing(self) -> str:
        return "https://www.{}/ap/maplanding".format(self.domain)

    def register(self) -> str:
        return "https://api.{}/auth/register".format(self.domain)

    def config(self) -> str:
        return "https://atv-ps.{}/cdp/usage/v2/GetAppStartupConfig".format(self.domain)

    def playback(self) -> str:
        if self.api is None:
            return None

        return "https://{}/cdp/catalog/GetPlaybackResources".format(self.api)
