"""

Wallbox class

"""

from datetime import datetime
from time import timezone
from requests.auth import HTTPBasicAuth
import requests
import json

from wallbox.bearerauth import BearerAuth


class Wallbox:
    def __init__(self, username, password, requestGetTimeout = None, jwtTokenDrift = 0):
        self.username = username
        self.password = password
        self._requestGetTimeout = requestGetTimeout
        self.baseUrl = "https://api.wall-box.com/"
        self.authUrl = "https://user-api.wall-box.com/"
        self.jwtTokenDrift = jwtTokenDrift
        self.jwtToken = ""
        self.jwtRefreshToken = ""
        self.jwtTokenTtl = 0
        self.jwtRefreshTokenTtl = 0
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
            "User-Agent": "HomeAssistantWallboxPlugin/1.0.0",
        }

    @property
    def requestGetTimeout(self):
        return self._requestGetTimeout

    def authenticate(self):
        auth_path = "users/signin"
        auth = HTTPBasicAuth(self.username, self.password)
        # if already has token:
        if self.jwtToken != "":
            # check if token is still valid
            if round((self.jwtTokenTtl / 1000) - self.jwtTokenDrift, 0) > datetime.timestamp(datetime.now()):
                return
            # if not, check if refresh token is still valid
            elif (self.jwtRefreshToken != ""
                  and round((self.jwtRefreshTokenTtl / 1000) - self.jwtTokenDrift, 0)
                  > datetime.timestamp(datetime.now())):
                # try to refresh token
                auth_path = "users/refresh-token"
                auth = BearerAuth(self.jwtRefreshToken)

        try:
            response = requests.get(
                f"{self.authUrl}{auth_path}",
                auth=auth,
                headers={'Partner': 'wallbox'},
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)

        self.jwtToken = json.loads(response.text)["data"]["attributes"]["token"]
        self.jwtRefreshToken = json.loads(response.text)["data"]["attributes"]["refresh_token"]
        self.jwtTokenTtl = json.loads(response.text)["data"]["attributes"]["ttl"]
        self.jwtRefreshTokenTtl = json.loads(response.text)["data"]["attributes"]["refresh_token_ttl"]
        self.headers["Authorization"] = f"Bearer {self.jwtToken}"

    def getChargersList(self):
        chargerIds = []
        try:
            response = requests.get(
                f"{self.baseUrl}v3/chargers/groups", headers=self.headers,
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        for group in json.loads(response.text)["result"]["groups"]:
            for charger in group["chargers"]:
                chargerIds.append(charger["id"])
        return chargerIds

    def getChargerStatus(self, chargerId):
        try:
            response = requests.get(
                f"{self.baseUrl}chargers/status/{chargerId}", headers=self.headers,
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def unlockCharger(self, chargerId):
        try:
            response = requests.put(
                f"{self.baseUrl}v2/charger/{chargerId}",
                headers=self.headers,
                data='{"locked":0}',
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def lockCharger(self, chargerId):
        try:
            response = requests.put(
                f"{self.baseUrl}v2/charger/{chargerId}",
                headers=self.headers,
                data='{"locked":1}',
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def setMaxChargingCurrent(self, chargerId, newMaxChargingCurrentValue):
        try:
            response = requests.put(
                f"{self.baseUrl}v2/charger/{chargerId}",
                headers=self.headers,
                data=f'{{ "maxChargingCurrent":{newMaxChargingCurrentValue}}}',
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def pauseChargingSession(self, chargerId):
        try:
            response = requests.post(
                f"{self.baseUrl}v3/chargers/{chargerId}/remote-action",
                headers=self.headers,
                data='{"action":2}',
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def resumeChargingSession(self, chargerId):
        try:
            response = requests.post(
                f"{self.baseUrl}v3/chargers/{chargerId}/remote-action",
                headers=self.headers,
                data='{"action":1}',
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def restartCharger(self, chargerId):
        try:
            response = requests.post(
                f"{self.baseUrl}v3/chargers/{chargerId}/remote-action",
                headers=self.headers,
                data='{"action":3}',
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def getSessionList(self, chargerId, startDate, endDate):
        try:
            payload = {'charger': chargerId, 'start_date': startDate.timestamp(), 'end_date': endDate.timestamp() }

            response = requests.get(
                f"{self.baseUrl}v4/sessions/stats", params=payload, headers=self.headers,
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def setEnergyCost(self, chargerId, energyCost):
        try:
            response = requests.post(
                f"{self.baseUrl}chargers/config/{chargerId}",
                headers=self.headers,
                json={'energyCost': energyCost},
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def getChargerSchedules(self, chargerId):
        try:
            response = requests.get(
                f"{self.baseUrl}chargers/{chargerId}/schedules", headers=self.headers,
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    """
    Example request:
    {
        'schedules': [{
            'id': 0,
            'chargerId': 42,
            'enable': 1,
            'max_current': 1,
            'max_energy': 0,
            'days': {'friday': True, 'monday': True, 'saturday': True, 'sunday': True, 'thursday': True,
                     'tuesday': True, 'wednesday': True},
            'start': '2100',
            'stop': '0500'
        }]
    }

    Where id is the position to add/replace
    """

    def setChargerSchedules(self, chargerId, newSchedules):
        try:
            # Enforce chargerId
            for schedule in newSchedules.get('schedules', []):
                schedule['chargerId'] = chargerId

            response = requests.post(
                f"{self.baseUrl}chargers/{chargerId}/schedules",
                headers=self.headers,
                json=newSchedules,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)
