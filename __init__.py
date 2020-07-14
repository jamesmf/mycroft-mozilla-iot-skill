from collections import defaultdict
from typing import List
import requests

from mycroft.skills.common_iot_skill import (
    CommonIoTSkill,
    IoTRequest,
    IoTRequestVersion,
    Thing,
    Action,
    Attribute,
    State,
)
from mycroft.skills.core import FallbackSkill
from mycroft.util.log import getLogger

LOG = getLogger()
LOG.info("BEGUN")

# from .mozilla_client import MozillaIoTClient

LOG.info("MADE IT PAST LOAD")

_MAX_BRIGHTNESS = 254


class MozillaIoTClient:
    def __init__(self, host: str, token: str):
        """
        Client for interacting with the Mozilla IoT API
        """
        LOG.info("init'd client")
        self.host = host
        self.headers = {
            "Authorization": "Bearer {}".format(token),
            "Content-Type": "application/json",
        }
        LOG.info("client get_things()")
        self.things = self.get_things()
        self.entity_names: List[str] = [
            thing["title"] for thing in self.things if "title" in thing
        ]
        LOG.info("finished client init")

    def _request(self, method: str, endpoint: str, data: dict = None):

        url = self.host + endpoint

        response = requests.request(method, url, json=data, headers=self.headers)

        response.raise_for_status()

        return response

    def get_things(self):
        if self.host:
            return self._request("GET", "/things/")
        return []


class MozillaIoTSkill(CommonIoTSkill, FallbackSkill):
    def __init__(self):
        super().__init__(name="MozillaIoTSkill")
        LOG.info("init'd skill")

        self._client: MozillaIoTClient = None
        self._entities = dict()
        self._scenes: List[str] = []
        LOG.info("init complete?")

    def initialize(self):
        LOG.info("beginning initialize")

        self.settings.set_changed_callback(self.on_websettings_changed)
        self._setup()
        self._entities: List[str] = self._client.entity_names
        self._scenes = []
        LOG.info("ABOUT TO REGISTER")
        self.register_entities_and_scenes()

    def _setup(self):
        self._client = MozillaIoTClient(
            token=self.settings.get("token"), host=self.settings.get("host")
        )

    def on_websettings_changed(self):
        self._setup()

    def get_entities(self):
        return self._entities

    def get_scenes(self):
        return []

    @property
    def supported_request_version(self) -> IoTRequestVersion:
        return IoTRequestVersion.V3
