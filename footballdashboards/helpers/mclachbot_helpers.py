"""
Helpers for getting data from the mclachbot API
"""

from urllib.request import urlopen
from PIL import Image
from urllib.error import HTTPError
import requests
import json

class McLachBotBadgeService:
    url = "http://www.mclachbot.com:9000"

    def league_badge(self, league: str) -> Image:
        """
        Get the imagine for a league from the sportsdb API

        Args:
            league (str): League to get the image for

        Returns:
            Image: Image of the league badge

        """
        league = league.replace(" ", "%20")

        url = f"{self.url}/league_badge_download/{league}"
        try:
            return Image.open(urlopen(url))
        except HTTPError as exc:
            raise ValueError(f"League {league} not found") from exc

    def team_badge(self, league: str, team: str) -> Image:
        """
        Get the imagine for a team from the sportsdb API

        Args:
            league (str): League to get the image for
            team (str): Team to get the image for

        Returns:
            Image: Image of the team badge

        """
        league = league.replace(" ", "%20")
        team = team.replace(" ", "%20")

        url = f"{self.url}/badge_download/{league}/{team}"
        try:
            return Image.open(urlopen(url))
        except HTTPError as exc:
            raise ValueError(f"Team {team} not found in league {league}") from exc


def get_ball_logo() -> Image:
    """
    Get the imagine for the ball logo from the sportsdb API

    Returns:
        Image: Image of the ball logo

    """
    url = "http://www.mclachbot.com/site/img/ball_logo.png"
    return Image.open(urlopen(url))



class TeamColorHelper:

    url = "http://www.mclachbot.com:9000"

    default_colours = ["#bbbbbb", "#000000"]


    def get_colours(self, league:str, team:str):
        league = league.replace(" ", "%20")
        team = team.replace(" ", "%20")
        full_url = f"{self.url}/colours/{league}/{team}"
        try:
            r = requests.get(full_url)
            if r.status_code == 200:
                colours = json.loads(r.text)
                if not colours[0] or colours[0] == "None":
                    return self.default_colours
                return colours
            else:
                return self.default_colours

        except HTTPError:
            return None