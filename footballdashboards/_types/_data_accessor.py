"""
This module provides a duck type for data accessor to use for type hinting.

"""
from abc import ABC, abstractmethod
import pandas as pd


class _DataAccessor(ABC):  # pylint: disable=too-few-public-methods
    """
    Defines a duck type for data accessor to use for type hinting.

    """

    @abstractmethod
    def get_data(self, data_requester_name: str, **kwargs) -> pd.DataFrame:
        """
        Function that takes the name of the dashboard that is requesting the data
        and a kwargs of parameters needed to retrieve the specific data and returns
        a pandas dataframe of the data.

        Args:
            data_requester_name (str): Name of the dashboard requesting the data
            kwargs: Parameters needed to retrieve the data

        Returns:
            pd.DataFrame: Dataframe of the data requesteds
        """
