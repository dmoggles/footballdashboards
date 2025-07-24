from matplotlib.axes import Axes
from mplsoccer import Pitch
from typing import List, Dict, Any
import pandas as pd
from footmav.utils import whoscored_funcs as WF
from footmav.data_definitions.whoscored.constants import EventType
from matplotlib.lines import Line2D
from footballdashboards.helpers.fonts import font_normal
from footballdashboards.helpers.pass_type_definitions import PassTypeDefinition
import matplotlib.patheffects as path_effects
from footballdashboards.helpers.event_definitions import (
    defensive_events,
    EventDefinition,
    get_touch_events,
)
from sklearn.ensemble import IsolationForest
import numpy as np
import math
from enum import Enum
from pydantic import BaseModel

class Layer(Enum):
    Complete = 'complete'
    Incomplete = 'incomplete'

class PlotConfig(BaseModel):
    pass_types: List[str] = []
    top_layer: Layer = Layer.Incomplete
    complete_alpha: float = 1.0
    incomplete_alpha: float = 1.0

def draw_passes_on_axes(ax: Axes, data: pd.DataFrame, pitch: Pitch, plot_config: PlotConfig):
    pass_types = plot_config.pass_types

    data = data.copy()
    data["passtypes"] = WF.classify_passes(data)
    passes = data.loc[
        (data["event_type"] == EventType.Pass)
        & (~WF.col_has_qualifier(data, qualifier_code=107))  # Not a throw in
    ]
    passtype_classes = [
        cls
        for cls in PassTypeDefinition.__subclasses__()
        if len(pass_types) == 0 or cls.__name__ in pass_types
    ]
    for passtype_class in passtype_classes:
        mask = passtype_class.mask(passes)
        select_passes = passes.loc[mask]
        if len(select_passes) > 0:
            kwargs = passtype_class.get_line_kwargs()
            if passtype_class.is_complete():
                kwargs["alpha"] = plot_config.complete_alpha
            else:
                kwargs["alpha"] = plot_config.incomplete_alpha
            if plot_config.top_layer == Layer.Complete:
                if passtype_class.is_complete():
                    kwargs['zorder'] = 10
                else:
                    kwargs['zorder'] = 5

            pitch.lines(
                select_passes["x"],
                select_passes["y"],
                select_passes["endX"],
                select_passes["endY"],
                label=passtype_class.label(),
                ax=ax,
                **kwargs,
            )


def draw_pass_legend_on_axes(
    ax: Axes,
    base_color: str,
    base_edge_color: str,
    loc: str = "lower left",
    pass_types: List[str] = None,
    label_kwargs: Dict[str, Any] = None,
    legend_kwargs: Dict[str, Any] = None,
):
    passtype_classes = [
        cls
        for cls in PassTypeDefinition.__subclasses__()
        if pass_types is None or cls.__name__ in pass_types
    ]
    handles = []
    label_kwargs = label_kwargs or {"marker": "o", "markersize": 5, "linewidth": 0}
    for passtype_class in passtype_classes:
        kwargs = passtype_class.get_line_kwargs()
        handles.append(
            Line2D(
                [0],
                [0],
                color=kwargs["color"],
                label=passtype_class.label().title(),
                **label_kwargs,
            )
        )

        legend_kwargs = legend_kwargs or dict(
            framealpha=1,
            labelspacing=0.5,
            fancybox=True,
            borderpad=0.25,
            handletextpad=0.1,
            prop=font_normal.prop,
            ncol=3,
        )

        ax.legend(
            handles=handles,
            loc=loc,
            facecolor=base_color,
            edgecolor=base_edge_color,
            labelcolor=base_edge_color,
            **legend_kwargs,
        )


def plot_positional_heatmap_on_pitch(
    ax,
    pitch,
    data,
    base_edge_color: str = "#ffffff",
    scatter_color: str = "blue",
    cmap="hot",
):
    passes_mask = (data["event_type"] == EventType.Pass) & (
        ~WF.col_has_qualifier(data, qualifier_code=107)
    )

    path_eff = [
        path_effects.Stroke(linewidth=3, foreground="white"),
        path_effects.Normal(),
    ]

    bin_statistic = pitch.bin_statistic_positional(
        data.loc[passes_mask].x,
        data.loc[passes_mask].y,
        statistic="count",
        positional="full",
        normalize=True,
    )
    pitch.heatmap_positional(bin_statistic, ax=ax, cmap=cmap, edgecolors=base_edge_color)
    pitch.scatter(
        data.loc[passes_mask].x,
        data.loc[passes_mask].y,
        c=scatter_color,
        s=2,
        ax=ax,
    )
    pitch.label_heatmap(
        bin_statistic,
        color=base_edge_color,
        fontsize=11,
        ax=ax,
        ha="center",
        va="center",
        str_format="{:.0%}",
        path_effects=path_eff,
        zorder=20,
    )


def apply_event_plot(
    pitch: Pitch,
    ax,
    data,
    event_definition: EventDefinition,
    size: int,
    base_color: str,
    base_edge_color: str,
):
    """Apply the event plot to the axes"""

    sub_data = data.loc[
        (data["event_type"] == event_definition.event_type)
        & (data["outcomeType"] == event_definition.outcome_type)
    ]

    pitch.scatter(
        sub_data["x"],
        sub_data["y"],
        marker=event_definition.marker,
        color=event_definition.color if event_definition.color else base_color,
        edgecolors=[event_definition.edge_color] * sub_data.shape[0]
        if event_definition.edge_color
        else [base_edge_color] * sub_data.shape[0],
        ax=ax,
        s=size * event_definition.size_mult,
        alpha=0.7,
        linewidth=1,
        zorder=10,
    )


def draw_defensive_events_on_axes(
    ax: Axes,
    data: pd.DataFrame,
    pitch: Pitch,
    base_size: float,
    base_color: str,
    base_edge_color: str,
):
    """Draw defensive events on the axes"""
    for event_type in defensive_events:
        apply_event_plot(pitch, ax, data, event_type, base_size, base_color, base_edge_color)


def draw_convex_hull_without_outliers_on_axes(
    ax: Axes,
    data: pd.DataFrame,
    pitch: Pitch,
    outlier_ratio: float = 0.1,
    color: str = "cornflowerblue",
):
    """Draw the convex hull without outliers on the axes"""
    model = IsolationForest(contamination=outlier_ratio, random_state=0)
    total_touches = get_touch_events(data)
    if total_touches.shape[0] <= 4:
        return None
    total_touches["include"] = model.fit_predict(total_touches[["x", "y"]])
    included = total_touches.loc[total_touches["include"] == 1]
    if included.shape[0] >= 4:
        hull = pitch.convexhull(
            included["x"],
            included["y"],
        )
        poly = pitch.polygon(hull, ax=ax, edgecolor=color, facecolor=color, alpha=0.3, zorder=3)
        return poly
    else:
        return None


def draw_defensive_event_legend(
    ax,
    base_color,
    base_edge_color,
    base_size,
    horizontal=True,
    split=1,
    loc="upper center",
    facecolor="white",
    **kwargs
):
    """Draw the defensive event legend"""

    ax.set_facecolor(facecolor)
    kwargs["facecolor"] = facecolor
    dict_of_events = {
        event.label: event for event in sorted(defensive_events, key=lambda x: x.label)
    }
    legend_artists = [
        Line2D(
            [0],
            [0],
            marker=event.marker,
            label=event.label,
            markerfacecolor=event.color if event.color else base_color,
            markeredgecolor=event.edge_color if event.edge_color else base_edge_color,
            linewidth=0,
            markersize=base_size * event.size_mult,
        )
        for event in dict_of_events.values()
    ]
    bbox_coords = (
        0 if "left" in loc else 1 if "right" in loc else 0.5,
        1 if "upper" in loc else 0 if "lower" in loc else 0.5,
    )

    ncol = math.ceil(len(dict_of_events) / split) if horizontal else split
    total_elements_to_add = ncol * split - len(dict_of_events)

    array_legends = np.array(
        legend_artists + [Line2D([0], [0], linewidth=0, label="")] * total_elements_to_add
    )

    array_legends = np.resize(array_legends, (split, ncol))
    array_legends = [v for v in array_legends.T.flatten().tolist() if v != 0]
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])
    ax.legend(
        handles=array_legends,
        loc=loc,
        bbox_to_anchor=bbox_coords,
        ncol=ncol,
        labelcolor=base_color,
        prop=font_normal.prop,
        **kwargs,
    )
    return ax
