import re
import urllib3
import json
import wmi
import requests
from requests.auth import HTTPBasicAuth


port_regex = re.compile(r'\"--app-port=(.+?)\"')
auth_regex = re.compile(r'\"--remoting-auth-token=(.+?)\"')


class LCU:
    def __init__(self):
        c = wmi.WMI()
        processes = c.Win32_Process(name="LeagueClientUX.exe")
        if len(processes) == 0:
            return
        command_line = processes[0].CommandLine
        self.port = port_regex.findall(command_line)[0]
        self.auth = auth_regex.findall(command_line)[0]
        # LCU doesn't have a valid SSL certificate
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def request(self, path, params=None):
        res = requests.get("https://127.0.0.1:" + self.port + path, params=params, auth=HTTPBasicAuth("riot", self.auth), verify=False)
        return res.json()

    def get_summoner_names(self, ids):
        params = {'ids': json.dumps(ids)}
        return self.request("/lol-summoner/v2/summoner-names", params=params)

    def get_champ_select_teammates(self):
        champ_select = self.request("/lol-champ-select/v1/session")
        # Error occurred
        if "myTeam" not in champ_select:
            return []

        ids = []
        teammates = []
        for player in champ_select["myTeam"]:
            ids.append(player["summonerId"])
            position = player["assignedPosition"]
            if position == "utility":
                position = "support"
            teammates.append({
                "assigned_role": position,
                "summoner_id": player["summonerId"]
            })

        names = self.get_summoner_names(ids)
        for i, name in enumerate(names):
            if name["summonerId"] != teammates[i]["summoner_id"]:
                raise
            teammates[i]["name"] = name["displayName"]

        return teammates
