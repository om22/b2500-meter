from .base import Powermeter
import requests
from typing import Union, List


class HomeAssistant(Powermeter):
    def __init__(
        self,
        ip: str,
        port: str,
        use_https: bool,
        access_token: str,
        current_power_entity: Union[str, List[str]],
        power_calculate: bool,
        power_input_alias: Union[str, List[str]],
        power_output_alias: Union[str, List[str]],
        path_prefix: str,
    ):
        self.ip = ip
        self.port = port
        self.use_https = use_https
        self.access_token = access_token
        self.current_power_entity = (
            [current_power_entity]
            if isinstance(current_power_entity, str)
            else current_power_entity
        )
        self.power_calculate = power_calculate
        self.power_input_alias = (
            [power_input_alias]
            if isinstance(power_input_alias, str)
            else power_input_alias
        )
        self.power_output_alias = (
            [power_output_alias]
            if isinstance(power_output_alias, str)
            else power_output_alias
        )
        self.path_prefix = path_prefix
        self.session = requests.Session()
        self._last_changed = []

    def get_json(self, path):
        if self.path_prefix:
            path = self.path_prefix + path
        if self.use_https:
            url = f"https://{self.ip}:{self.port}{path}"
        else:
            url = f"http://{self.ip}:{self.port}{path}"
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "content-type": "application/json",
        }
        return self.session.get(url, headers=headers, timeout=10).json()

    def has_changed(self):
        last_changed = []

        if not self.power_calculate:
            for entity in self.current_power_entity:
                path = f"/api/states/{entity}"
                response = self.get_json(path)
                last_changed.append(response["last_changed"])
        else:
            for in_entity, out_entity in zip(self.power_input_alias, self.power_output_alias):
                response_in = self.get_json(f"/api/states/{in_entity}")
                response_out = self.get_json(f"/api/states/{out_entity}")
                last_changed.append((response_in["last_changed"], response_out["last_changed"]))

        if last_changed == self._last_changed:
            return False

        self._last_changed = last_changed
        return True

    def get_powermeter_watts(self):
        if not self.power_calculate:
            results = []
            for entity in self.current_power_entity:
                path = f"/api/states/{entity}"
                response = self.get_json(path)
                results.append(float(response["state"]))
            return results
        else:
            results = []
            for in_entity, out_entity in zip(
                self.power_input_alias, self.power_output_alias
            ):
                response = self.get_json(f"/api/states/{in_entity}")
                power_in = float(response["state"])
                response = self.get_json(f"/api/states/{out_entity}")
                power_out = float(response["state"])
                results.append(power_in - power_out)
            return results
