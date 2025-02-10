from dataclasses import dataclass, field
from typing import Any, Dict, Callable, List, Tuple
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from mplsoccer.pitch import Pitch


@dataclass
class GraphicComponents:
    figure: Figure
    axes: Dict[str, Axes]
    pitches: Dict[str, Pitch]


@dataclass
class GraphicConfig:
    data_function: Callable[[Dict[str, Any]], pd.DataFrame]
    
    layout_function: Callable[[Dict[str, Any]], GraphicComponents]
    plots: Dict[str, Callable[[Dict[str, Any], pd.DataFrame, Figure, Axes, Pitch], None]]
    pitch_map: Dict[str, str]
    plotting_config: Dict[str, Any]
    data_filters: List[Tuple[str, Any]] = field(default_factory=list)


def plot_graphic(graphic_config: GraphicConfig) -> Figure:
    data = graphic_config.data_function(graphic_config.plotting_config)
    layout = graphic_config.layout_function(graphic_config.plotting_config)
    for plot_name, plot_function in graphic_config.plots.items():
        plot_function(
            graphic_config.plotting_config,
            data,
            layout.figure,
            layout.axes[plot_name],
            layout.pitches[graphic_config.pitch_map[plot_name]],
            graphic_config.data_filters
        )
    return layout.figure
