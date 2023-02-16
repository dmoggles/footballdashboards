"""
Mixins that define specific parameters for getting data from the datasource.

These are responsible for ultimately generating the user facing
plotting API
"""

from typing import TYPE_CHECKING, List
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards.dashboard.dashboard import Dashboard

if TYPE_CHECKING:
    _Base = Dashboard
else:
    _Base = object


class SeasonLeagueMixin(_Base):  # pylint: disable=too-few-public-methods
    """
    Mixin that defines the season and league parameters for the data accessor
    """

    def plot_seasons_leagues(self, seasons: List[int], leagues: List[str]) -> PlotReturnType:
        """
        Function that gets the data for given leagues and seasons

        Args:
            seasons (List[int]): List of seasons to get data for
            leagues (List[str]): List of leagues to get data for

        Returns:
            PlotReturnType: Plotting data
        """
        return self._plot(seasons=seasons, leagues=leagues)


class PlayerSeasonsLeaguesMixin(_Base):  # pylint: disable=too-few-public-methods
    """
    Mixin that defines the player, season and league parameters for the data accessor
    """

    def plot_player_seasons_leagues(
        self, player: str, seasons: List[int], leagues: List[str]
    ) -> PlotReturnType:
        """
        Function that gets the data for given player, leagues and seasons

        Args:
            player (str): Player to get data for
            seasons (List[int]): List of seasons to get data for
            leagues (List[str]): List of leagues to get data for

        Returns:
            PlotReturnType: Plotting data
        """
        return self._plot(player=player, seasons=seasons, leagues=leagues)
