"""
And example datasource for use with the sample dashboards.

Reads csv files from the examples folder.

"""
import os
import pandas as pd


class SampleDatasource:
    """
    Example datasource for use with the sample dashboards.
    """

    EXAMPLE_DICT = {"ScatterDashboard": "scatter_example.csv"}

    @classmethod
    def get_data(cls, data_requester_name: str, **_) -> pd.DataFrame:
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
        return pd.read_csv(
            os.path.join(
                os.path.dirname(__file__), "data_samples", cls.EXAMPLE_DICT[data_requester_name]
            )
        )
