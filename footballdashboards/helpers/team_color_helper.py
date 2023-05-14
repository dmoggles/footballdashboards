import requests
import json
from urllib.error import HTTPError

class TeamColorHelper:

    url = "http://www.mclachbot.com:9000"

    default_colours = ["#bbbbbb", "#000000"]


    def get_colours(self, league:str, team:str):
        league = league.replace(" ", "%20")
        team = team.replace(" ", "%20")
        url = f"http://www.mclachbot.com:9000/colours/{league}/{team}"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                colours = json.loads(r.text)
                if not colours[0] or colours[0] == "None":
                    return self.default_colours
                return colours
            else:
                return self.default_colours

        except HTTPError:
            return None