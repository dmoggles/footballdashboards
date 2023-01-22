"""
Defines the abstract Dashboard base class which provides common functionality
to all dashboards.
"""

from abc import ABC, abstractmethod
from typing import List
import pandas as pd
from footballdashboards._types._data_accessor import _DataAccessor
from footballdashboards._types._dashboard_fields import ColorField
from footballdashboards._defaults._colours import FIGURE_FACECOLOUR, TEXT_COLOUR
from footballdashboards._types._custom_types import PlotReturnType


class Dashboard(ABC):
    """
    Dashboard ABC which all dashboard visualizations must inherit from.

    Specifies most of the metadata functions that inheritors use to define their
    behavior

    """

    facecolor = ColorField(FIGURE_FACECOLOUR)
    textcolor = ColorField(TEXT_COLOUR)

    def __init__(self, data_accessor: _DataAccessor):
        """
        Initializes the dashboard with a data accessor

        data accessor class must implement the following methods:
            - get_data(self, data_requester_name: str, **kwargs) -> pd.DataFrame

        Args:
            data_accessor (_DataAccessor): Data accessor to use for retrieving data
        """
        self.data_accessor = data_accessor

    @abstractmethod
    def _required_data_columns(self) -> List[str]:
        """
        Function that returns a list of required data columns

        Returns:
            List[str]: List of required data columns
        """

    @abstractmethod
    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        """
        Function that plots the data

        Args:
            data (pd.DataFrame): Data to plot
        """

    def _plot(self, **kwargs) -> PlotReturnType:
        """
        Function that plots the dashboard

        Args:
            kwargs: Keyword arguments to pass to the plot function
        """
        data = self.data_accessor.get_data(self.__class__.__name__, **kwargs)
        self._validate_data(data)
        return self._plot_data(data, **kwargs)

    def _validate_data(self, data: pd.DataFrame):
        """
        Function that validates the data passed to the dashboard

        Args:
            data (pd.DataFrame): Data to validate

        Raises:
            AssertError: If the data is not valid
        """
        assert isinstance(data, pd.DataFrame), "Data must be a pandas dataframe"
        assert all(column in data.columns for column in self._required_data_columns()), (
            "Data must contain all required columns. "
            "The following columns are missing: "
            f"{set(self._required_data_columns()) - set(data.columns)}"
        )

    def match_plot(self, match_date: pd.Timestamp, team: str) -> PlotReturnType:
        """
        Function that plots the dashboard for a specific match and team

        Args:
            match_date (pd.Timestamp): Date of the match
            team (str): Team to plot

        Returns:
            PlotReturnType: Figure and dictionary of Axes of the dashboard
        """
        return self._plot(match_date=match_date, team=team)

    def player_season_plot(self, player: str, league: str, season: int) -> PlotReturnType:
        """
        Function that plots the dashboard for a specific player, league and season

        Args:
            player (str): Name of the player
            league (str): Name of the league
            season (int): Season to plot

        Returns:
            PlotReturnType: Figure and dictionary of Axes of the dashboard

        """
        return self._plot(player=player, league=league, season=season)
