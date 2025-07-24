from typing import Any, Dict, List, Tuple
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from mplsoccer.pitch import Pitch
from footballmodels.opta.event_type import EventType
from footmav.data_definitions.whoscored.constants import EventType as EventTypeOld
from footballdashboards.helpers.pitch_helpers import draw_passes_on_axes, PlotConfig
from footballdashboards.dashboard.player_maps.filter_applicator import apply_filters




def draw_passes(config: Dict[str, Any], data: pd.DataFrame, figure: Figure, ax: Axes, pitch: Pitch, filters: List[Tuple[str, Any]]):
    data = data.loc[data["event_type"] == EventType.Pass].copy()
    data = apply_filters(filters, data)
    data["event_type"] = EventTypeOld.Pass

    if len(data) > 0:
        if 'pass_map_config' in config:
            pass_config = PlotConfig.model_validate(config['pass_map_config'])
        else:
            pass_config = PlotConfig(pass_types=config.get('pass_types', []))
        draw_passes_on_axes(ax, data, pitch, pass_config)
