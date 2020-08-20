from collections import defaultdict
from typing import List, Dict, Union, Optional
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


def normalize(name: str) -> str:
    return name.lower().strip()


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
            normalize(thing["title"]) for thing in self.things if "title" in thing
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

    def get_set_value_request(
        self, entity: str, attribute: Optional[str], value: Union[str, int, float, None]
    ):
        """
        Attempt to set a thing's property value
        """
        things = [th for th in self.things if normalize(th["title"]) == entity]
        if len(things) == 0:
            return False, "", {}
        thing = things[0]
        LOG.info(json.dumps(thing, indent=2))
        # assume if we have no attribute that we're talking about a 'level' (for now)
        if attribute is None:
            attribute = "level"
        for prop, prop_dict in thing.get("properties", {}).items():
            if attribute in (normalize(prop), normalize(prop_dict["title"])):
                url = prop_dict.get("links", [{}])[0].get("href", "")
                data = {prop: value}
                cb = {"url": url, "data": data, "method": "PUT"}
                return True, cb
        return False, {}


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
        can_handle = False
        callback = {}
        if request.action == Action.SET and request.entity in self._entities:
            can_handle, callback = self._client.get_set_value_request(
                request.entity, request.attribute, request.value
            )

        return can_handle, callback

    def run_request(self, request, cb):
        LOG.info(str(request), request)
        LOG.info(cb)
        self._client._request(cb["method"], cb["url"], cb["data"])


def create_skill():
    return MozillaIoTSkill()
