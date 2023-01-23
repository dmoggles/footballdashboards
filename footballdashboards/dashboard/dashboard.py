"""
Defines the abstract Dashboard base class which provides common functionality
to all dashboards.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import pandas as pd
from footballdashboards._types._data_accessor import _DataAccessor
from footballdashboards._types._dashboard_fields import ColorField
from footballdashboards._defaults._colours import FIGURE_FACECOLOUR, TEXT_COLOUR
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService


class Dashboard(ABC):  # pylint: disable=too-few-public-methods
    """
    Dashboard ABC which all dashboard visualizations must inherit from.

    Specifies most of the metadata functions that inheritors use to define their
    behavior

    """

    field_descriptor_list: Dict[str, List[Tuple[str, str]]] = {}

    facecolor = ColorField(description="Figure background colour", default=FIGURE_FACECOLOUR)
    textcolor = ColorField(description="Figure text colour", default=TEXT_COLOUR)
    badge_service = McLachBotBadgeService()

    @classmethod
    def get_full_field_descriptor_list(cls) -> List[Tuple[str, str]]:
        """
        Function that returns the full field descriptor list

        Returns:
            List[Tuple[str, str]]: Full field descriptor list
        """
        _descriptors = cls.field_descriptor_list[cls.__name__].copy()
        for parent in cls.__bases__:
            if hasattr(parent, "get_full_field_descriptor_list"):
                _descriptors.extend(parent.get_full_field_descriptor_list())

        return _descriptors

    def __init__(self, data_accessor: _DataAccessor):
        """
        Initializes the dashboard with a data accessor

        data accessor class must implement the following methods:
            - get_data(self, data_requester_name: str, **kwargs) -> pd.DataFrame

        Args:
            data_accessor (_DataAccessor): Data accessor to use for retrieving data
        """
        self.data_accessor = data_accessor

    @property
    @abstractmethod
    def datasource_name(self) -> str:
        """
        Function that returns the name of the datasource

        Returns:
            str: Name of the datasource
        """

    @abstractmethod
    def _required_data_columns(self) -> Dict[str, str]:
        """
        Function that returns a listing of the required data columns
        and a description of each column

        Returns:
            Dict[str, str]: Dictionary of required data columns and their descriptions
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
        data = self.data_accessor.get_data(self.datasource_name, **kwargs)
        self._validate_data(data)
        return self._plot_data(data)

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

    def describe_adjustable_fields(self) -> Dict[str, str]:
        """
        Function that returns a dictionary of the adjustable fields and their descriptions

        Returns:
            Dict[str, str]: Dictionary of adjustable fields and their descriptions
        """
        descriptor_list = self.get_full_field_descriptor_list()
        descriptors = {
            field[0]: f"{field[1]}. Current value: {getattr(self, field[0])}"
            for field in descriptor_list
        }

        return descriptors
