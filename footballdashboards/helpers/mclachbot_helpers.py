"""
Helpers for getting data from the mclachbot API
"""

from urllib.request import urlopen
from PIL import Image
from urllib.error import HTTPError


class McLachBotBadgeService:
    def league_badge(self, league: str) -> Image:
        """
        Get the imagine for a league from the sportsdb API

        Args:
            league (str): League to get the image for

        Returns:
            Image: Image of the league badge

        """
        league = league.replace(" ", "%20")

        url = f"http://www.mclachbot.com:9000/league_badge_download/{league}"
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

        url = f"http://www.mclachbot.com:9000/badge_download/{league}/{team}"
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