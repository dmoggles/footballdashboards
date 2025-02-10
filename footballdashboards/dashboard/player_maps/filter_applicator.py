from typing import List, Tuple, Any
import pandas as pd
from footballdashboards.dashboard.player_maps import filters
def apply_filters(filter_params:List[Tuple[str, Any]], data:pd.DataFrame)->pd.DataFrame:
    for filter_name, params in filter_params:
        if hasattr(filters, filter_name):
            data = getattr(filters, filter_name)(data, params)
    return data