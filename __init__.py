from collections import defaultdict
from typing import List, Dict, Union
import requests
import json

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


_MAX_BRIGHTNESS = 254


class MozillaIoTClient:
    def __init__(self, host: str, token: str):
        """
        Client for interacting with the Mozilla IoT API
        """
        LOG.info("init'd client")
        if host[-1] == "/":
            host = host[:-1]
        self.host = host
        self.headers = {
            "Authorization": "Bearer {}".format(token),
            "Content-Type": "application/json",
        }
        LOG.info("client get_things()")
        self.things = self.get_things()
        self.entity_names: List[str] = [
            thing["title"].lower().strip() for thing in self.things if "title" in thing
        ]
        LOG.info("finished client init")

    def _request(self, method: str, endpoint: str, data: dict = None):

        url = self.host + endpoint
        LOG.info(url)
        response = requests.request(method, url, json=data, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("caught: ", e)

        return response

    def get_things(self):
        if self.host:
            resp = self._request("GET", "/things/")
            print(resp)
            return resp.json()
        return []

    def set_value(self, entity: str, attribute: str, value: Union[str, int, float]):
        """
        Attempt to set a thing's property value
        """
        thing = [th for th in self.things if th["title"] == entity]
        LOG.info(json.dumps(thing))


class MozillaIoTSkill(CommonIoTSkill, FallbackSkill):
    def __init__(self):
        LOG.info("init'd skill")
        super().__init__(name="MozillaIoTSkill")

        self._client: MozillaIoTClient = None
        self._entities = []
        self._scenes: List[str] = []

    def initialize(self):
        LOG.info("beginning initialize")

        self.settings_change_callback = self.on_websettings_changed
        self._setup()

    def _setup(self):
        self._client = MozillaIoTClient(
            token=self.settings.get("token"), host=self.settings.get("host")
        )
        print("client initialized")
        self._entities: List[str] = self._client.entity_names
        self._scenes = []
        LOG.info(f"Entities Registered: {self._entities}")
        self.register_entities_and_scenes()

    def on_websettings_changed(self):
        self._setup()

    def get_entities(self):
        return self._entities

    def get_scenes(self):
        return []

    @property
    def supported_request_version(self) -> IoTRequestVersion:
        return IoTRequestVersion.V3

    def can_handle(self, request):
        LOG.info("Mozilla IoT was consulted")
        LOG.info(request)
        if request.action == Action.SET and request.entity in self._entities:
            self._client.set_value(request.entity, request.attribute, request.value)

        return True, {}

    def run_request(self, request, cb):
        LOG.info(str(request), request)


def create_skill():
    return MozillaIoTSkill()
