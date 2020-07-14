import requests
from typing import List


class MozillaIoTClient:
    def __init__(self, host: str, token: str):
        """
        Client for interacting with the Mozilla IoT API
        """
        self.host = host
        self.headers = {
            "Authorization": "Bearer {}".format(token),
            "Content-Type": "application/json",
        }
        self.things = self.get_things()
        self.entity_names: List[str] = [
            thing["title"] for thing in self.things if "title" in thing
        ]

    def _request(self, method: str, endpoint: str, data: dict = None):

        url = self.host + endpoint

        response = requests.request(method, url, json=data, headers=self.headers)

        response.raise_for_status()

        return response

    def get_things(self):
        if self.host:
            return self._request("GET", "/things/")
        return []
