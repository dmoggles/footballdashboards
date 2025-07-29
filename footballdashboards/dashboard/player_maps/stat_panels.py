from typing import Any, Dict, Type, List
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from mplsoccer.pitch import Pitch
from footballmodels.xt.calcs import net_xt
from footballdashboards.helpers.fonts import font_bold, font_normal
from matplotlib import colormaps
from footballmodels.xpass.models import get_model
from footballmodels.xpass.features import x_pass_features_v2
from footballmodels.opta.event_type import EventType
from footmav.data_definitions.whoscored.constants import EventType as EventTypeOld
from footmav.utils import whoscored_funcs as WF
from footballdashboards.helpers.pass_type_definitions import (
    RegularPassComplete,
    RegularPassIncomplete,
    ProgressivePassComplete,
    ProgressivePassIncomplete,
    CutbacksComplete,
    CutbacksIncomplete,
    PassTypeDefinition,
)
from footballdashboards.dashboard.player_maps.helpers import calc_minutes
from footballdashboards.helpers.mclachbot_helpers import get_ball_logo2
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.dashboard.player_maps.filter_applicator import apply_filters

def _create_pass_type_class(
    color: str, z_order: int, base_class: Type[PassTypeDefinition]
) -> PassTypeDefinition:
    class NewPassType(base_class):
        @classmethod
        def _line_kwargs(cls):
            values = base_class._line_kwargs()
            values["color"] = color
            values["zorder"] = z_order
            return values

    return NewPassType


def draw_passing_stats(
    config: Dict[str, Any], data: pd.DataFrame, figure: Figure, ax: Axes, pitch: Pitch, filters: List[str]
):
    minutes = calc_minutes(data)
    complete_passes = [
        ("Regular", RegularPassComplete),
        ("Progressive", ProgressivePassComplete),
        ("Cutbacks", CutbacksComplete),
    ]
    incomplete_passes = [
        ("Regular", RegularPassIncomplete),
        ("Progressive", ProgressivePassIncomplete),
        ("Cutbacks", CutbacksIncomplete),
    ]
    data = data[data["event_type"] == EventType.Pass].copy()
    data["xt"] = net_xt(data) * data["outcomeType"]
    data = apply_filters(filters, data)
    data["event_type"] = EventTypeOld.Pass
    data["passtypes"] = WF.classify_passes(data)
    passes = data.loc[
        (data["event_type"] == EventTypeOld.Pass)
        & (~WF.col_has_qualifier(data, qualifier_code=107))  # Not a throw in
    ]

    ax.text(
        0.0,
        0.95,
        "Passing Stats",
        ha="left",
        va="center",
        fontsize=12,
        fontproperties=font_bold.prop,
        color="black",
        transform=ax.transAxes,
    )
    start_y = 0.92
    for i, (pass_type, pass_class) in enumerate(complete_passes):

        incomplete_class = incomplete_passes[i][1]
        complete_pass_count = passes[pass_class.mask(passes)].shape[0]
        incomplete_pass_count = passes[incomplete_class.mask(passes)].shape[0]
        complete_color = pass_class.get_line_kwargs()["color"]
        incomplete_color = incomplete_class.get_line_kwargs()["color"]

        ax.text(
            0.0,
            start_y - i * 0.09,
            f"{pass_type} Passes",
            ha="left",
            va="center",
            fontsize=10,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        ax.text(
            0.0,
            start_y - i * 0.09 - 0.02,
            "Complete",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color=complete_color,
            transform=ax.transAxes,
        )
        ax.text(
            0.0,
            start_y - i * 0.09 - 0.04,
            f"Incomplete",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color=incomplete_color,
            transform=ax.transAxes,
        )
        ax.text(
            0.0,
            start_y - i * 0.09 - 0.06,
            f"% Complete",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        ax.text(
            0.5,
            start_y - i * 0.09 - 0.02,
            f"{complete_pass_count}",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        ax.text(
            0.5,
            start_y - i * 0.09 - 0.04,
            f"{incomplete_pass_count}",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        pct = (
            complete_pass_count / (complete_pass_count + incomplete_pass_count)
            if complete_pass_count + incomplete_pass_count > 0
            else 0
        )
        ax.text(
            0.5,
            start_y - i * 0.09 - 0.06,
            f"{pct:.2%}",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        section_end = start_y - i * 0.09 - 0.08
    start_y = section_end - 0.02
    ax.text(
        0,
        start_y,
        "Advanced Stats",
        ha="left",
        va="center",
        fontsize=12,
        fontproperties=font_bold.prop,
        color="black",
        transform=ax.transAxes,
    )
    ax.text(
        0,
        start_y - 0.04,
        "Expected Threat",
        ha="left",
        va="center",
        fontsize=10,
        fontproperties=font_normal.prop,
        color="black",
        transform=ax.transAxes,
    )
    ax.text(
        0,
        start_y - 0.06,
        "Total xT p90",
        ha="left",
        va="center",
        fontsize=9,
        fontproperties=font_normal.prop,
        color="black",
        transform=ax.transAxes,
    )
    ax.text(
        0.5,
        start_y - 0.06,
        f"{data['xt'].sum()/minutes*90:.2f}",
        ha="left",
        va="center",
        fontsize=9,
        fontproperties=font_normal.prop,
        color="black",
        transform=ax.transAxes,
    )
    ax.text(
        0,
        start_y - 0.08,
        "Fwd xT p90",
        ha="left",
        va="center",
        fontsize=9,
        fontproperties=font_normal.prop,
        color="black",
        transform=ax.transAxes,
    )
    ax.text(
        0.5,
        start_y - 0.08,
        f"{data[data['xt']>0]['xt'].sum()/minutes*90:.2f}",
        ha="left",
        va="center",
        fontsize=9,
        fontproperties=font_normal.prop,
        color="black",
        transform=ax.transAxes,
    )
    start_y = start_y - 0.12
    try:
        model = get_model(data["competition"].iloc[0], True)
    except ValueError:
        model = get_model('epl')
    if model:
        features, _ = x_pass_features_v2(passes, True)
        passes["xPass"] = model.predict_proba(features)[:, 1]
        ax.text(
            0,
            start_y,
            "xPass",
            ha="left",
            va="center",
            fontsize=10,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        pass_pct = passes[passes["outcomeType"] == 1].shape[0] / passes.shape[0]
        pct_expected = passes["xPass"].sum() / passes.shape[0]
        ax.text(
            0,
            start_y - 0.02,
            "% Complete",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        ax.text(
            0.5,
            start_y - 0.02,
            f"{pass_pct:.2%}",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        ax.text(
            0,
            start_y - 0.04,
            r"% Expected",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        ax.text(
            0.5,
            start_y - 0.04,
            f"{pct_expected:.2%}",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        xpass_plus = pass_pct - pct_expected
        norm = max(min((xpass_plus + 0.05) / 0.1, 1), 0) * 0.5 + 0.5
        print(norm)

        color = colormaps["brg_r"](norm)
        ax.text(
            0,
            start_y - 0.06,
            "xPass+",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color="black",
            transform=ax.transAxes,
        )
        ax.text(
            0.5,
            start_y - 0.06,
            f"{xpass_plus:.2%}",
            ha="left",
            va="center",
            fontsize=9,
            fontproperties=font_normal.prop,
            color=color,
            transform=ax.transAxes,
        )

    logo_axis = ax.inset_axes([0, 0.03, 1, 1 / get_aspect(ax)], zorder=0.1)
    logo_axis.axis("off")
    logo_axis.imshow(get_ball_logo2(), alpha=1)
