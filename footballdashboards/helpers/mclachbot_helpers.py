"""
Helpers for getting data from the mclachbot API
"""

from typing import Any
from urllib.request import urlopen
from PIL import Image
from urllib.error import HTTPError
import requests
import json
import os


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


def get_ball_logo(url: str = "http://www.mclachbot.com/site/img/ball_logo.png") -> Image:
    """
    Get the imagine for the ball logo from the sportsdb API

    Returns:
        Image: Image of the ball logo

    """
    return Image.open(urlopen(url))


def get_ball_logo2(url: str = "http://www.mclachbot.com/site/img/mclachbot_logo.png") -> Image:
    """
    Get the imagine for the ball logo from the sportsdb API

    Returns:
        Image: Image of the ball logo

    """
    return Image.open(urlopen(url))


def get_image(url: str) -> Image:
    """
    Get the image

    Returns:
        Image: Image

    """
    return Image.open(urlopen(url))


class TeamColorHelper:
    url = "http://www.mclachbot.com:9000"

    default_colours = ["#bbbbbb", "#000000"]

    def get_colours(self, league: str, team: str):
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


class CachedPlayerImageHelper:
    url = "http://www.mclachbot.com:9000"

    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir

    def _check_cached_dir(self) -> bool:
        if not self.cache_dir:
            return False
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        return True

    def _check_cached_image(self, player_id: int) -> bool:
        if not self.cache_dir:
            return False
        if not os.path.exists(self.cache_dir):
            return False
        if not os.path.exists(os.path.join(self.cache_dir, f"{player_id}.png")):
            return False
        return True

    def _get_cached_image(self, player_id: int) -> Any:
        if not self.cache_dir:
            return None
        if not os.path.exists(self.cache_dir):
            return None
        if not os.path.exists(os.path.join(self.cache_dir, f"{player_id}.png")):
            return None
        return Image.open(os.path.join(self.cache_dir, f"{player_id}.png"))

    def _get_player_image(self, player_id: int) -> Any:
        full_url = f"{self.url}/player_cutout/{player_id}"
        try:
            r = requests.get(full_url)
            if r.status_code == 200:
                img = Image.open(urlopen(full_url))
                if self._check_cached_dir():
                    img.save(os.path.join(self.cache_dir, f"{player_id}.png"))
                return img
            else:
                return None

        except HTTPError:
            return None

    def get_player_image(self, player_id: int) -> Any:
        if self._check_cached_image(player_id):
            return self._get_cached_image(player_id)
        else:
            return self._get_player_image(player_id)
