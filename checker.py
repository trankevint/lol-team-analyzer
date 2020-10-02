import requests
import roleml
import time


class Checker:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_account_history(self, name, days):
        account_id = self.get_account_id_from_name(name)
        match_history = self.get_match_history(account_id, days)
        if match_history is None:
            return None
        analysis = self.analyze_match_history(account_id, match_history)
        return analysis

    def get_account_id_from_name(self, name):
        payload = {"api_key": self.api_key}
        r = requests.get(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{name}", params=payload)
        j = r.json()
        return j["accountId"]

    def get_match_history(self, account_id, days):
        current_time = int(time.time() * 1000)
        begin_time = current_time - (86400000 * days)
        payload = {"queue": "420", "beginTime": begin_time, "api_key": self.api_key}
        r = requests.get(f"https://na1.api.riotgames.com/lol/match/v4/matchlists/by-account/{account_id}", params=payload)
        j = r.json()
        return j if "matches" in j else None

    def analyze_match_history(self, account_id, match_history):
        role_list = []
        outcome_list = []
        payload = {"api_key": self.api_key}
        for match in match_history["matches"]:
            match_id = match["gameId"]
            match_r = requests.get(f"https://na1.api.riotgames.com/lol/match/v4/matches/{match_id}", params=payload)
            match_j = match_r.json()
            timeline_r = requests.get(f"https://na1.api.riotgames.com/lol/match/v4/timelines/by-match/{match_id}", params=payload)
            timeline_j = timeline_r.json()
            participant_id = self.get_participant_id(account_id, match_j)
            try:
                role = roleml.predict(match_j, timeline_j)[participant_id]
                role_list.append(role)
                game_outcome = self.get_game_outcome(participant_id, match_j)
                outcome_list.append(game_outcome)
            # Match was less than 15 minutes
            except:
                continue
        return self.get_main_role(role_list), self.get_win_loss(outcome_list)

    def get_participant_id(self, account_id, match_json):
        for participant in match_json["participantIdentities"]:
            if participant["player"]["accountId"] == account_id:
                return participant["participantId"]

    def get_game_outcome(self, participant_id, match_json):
        team = match_json["participants"][participant_id - 1]["teamId"]
        return match_json["teams"][0]["win"] if team == 100 else match_json["teams"][1]["win"]

    def get_main_role(self, match_list):
        info_d = dict()
        main_role, count = "", 0
        for role in match_list:
            info_d[role] = info_d.get(role, 0) + 1
            if info_d[role] >= count:
                main_role, count = role, info_d[role]
        return main_role

    def get_win_loss(self, outcome_list):
        return outcome_list.count("Win"), outcome_list.count("Fail")
