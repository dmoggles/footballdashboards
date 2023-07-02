"""
Functions for styling various headers on a given axis.
"""
from typing import Dict, Any, List
from matplotlib.axes import Axes
from footballdashboards.helpers.fonts import font_bold, font_italic
from matplotlib.patches import FancyBboxPatch
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.helpers.formatters import format_date
from footballdashboards.helpers.fonts import font_normal, font_mono
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService


def simple_title_subtitle_header(
    axis: Axes,
    title: str,
    subtitle: str,
    title_kwargs: Dict[str, Any],
    subtitle_kwargs: Dict[str, Any],
):

    """
    Simple header with title and subtitle
    """
    axis.text(
        0.5,
        0.5,
        title,
        ha=title_kwargs.get("ha", "center"),
        va=title_kwargs.get("va", "center"),
        fontproperties=font_bold.prop,
        **title_kwargs,
    )
    if subtitle:
        axis.text(
            0.5,
            -0.2,
            subtitle,
            ha=subtitle_kwargs.get("ha", "center"),
            va=subtitle_kwargs.get("va", "center"),
            fontproperties=font_italic.prop,
            **subtitle_kwargs,
        )


def match_dashboard_header(
    ax: Axes,
    date: str,
    league: str,
    teams: List[str],
    team_image_names: List[str],
    scores: List[int],
    formations: List[str],
    edgecolor: str,
    facecolor: str,
    sublabel_color: str,
    home_away: str = None,
):
    aspect = get_aspect(ax)
    ax.set_xlim(0, 1)
    y_max = 1 * aspect
    ax.set_ylim(0, y_max)
    rounded_bbox = FancyBboxPatch(
        (0.02, 0.02),
        0.96,
        y_max - 0.04,
        boxstyle="round,pad=0.02",
        ec=edgecolor,
        fc=facecolor,
        zorder=100,
        transform=ax.transData,
        lw=2,
    )
    ax.text(
        x=0.5,
        y=y_max * 0.95,
        s=format_date(date),
        ha="center",
        va="top",
        size=10,
        fontproperties=font_normal.prop,
        color=sublabel_color,
        zorder=101,
    )
    league_str = league
    if home_away:
        league_str += f" ({home_away})"

    ax.text(
        x=0.5,
        y=y_max * 0.05,
        s=league_str,
        ha="center",
        va="bottom",
        size=10,
        fontproperties=font_normal.prop,
        color=sublabel_color,
        zorder=101,
    )
    ax.text(
        x=0.5,
        y=y_max * 0.5,
        s=f"{scores[0]} - {scores[1]}",
        ha="center",
        va="center",
        size=20,
        fontproperties=font_mono.prop,
        color=edgecolor,
        zorder=101,
    )

    ax.text(
        x=0.11,
        y=y_max * 0.5,
        s=teams[0],
        ha="left",
        va="center",
        size=16,
        fontproperties=font_bold.prop,
        color=edgecolor,
        zorder=101,
    )
    ax.text(
        x=0.89,
        y=y_max * 0.5,
        s=teams[1],
        ha="right",
        va="center",
        size=16,
        fontproperties=font_bold.prop,
        color=edgecolor,
        zorder=101,
    )

    if formations:
        if not "-" in formations[0]:
            formations = ["-".join([k for k in f]) for f in formations]
        ax.text(
            x=0.11,
            y=y_max * 0.2,
            s=formations[0],
            ha="left",
            va="center",
            size=12,
            fontproperties=font_normal.prop,
            color=edgecolor,
            zorder=101,
        )
        ax.text(
            x=0.89,
            y=y_max * 0.2,
            s=formations[1],
            ha="right",
            va="center",
            size=12,
            fontproperties=font_normal.prop,
            color=edgecolor,
            zorder=101,
        )
    team_ax = ax.inset_axes((0.02, 0.04, aspect * 0.92, 0.92), zorder=200)
    team_ax.axis("off")
    team_ax.imshow(McLachBotBadgeService().team_badge(league, team_image_names[0]))
    opponent_ax = ax.inset_axes((1 - 0.02 - aspect * 0.92, 0.04, aspect * 0.92, 0.92), zorder=200)
    opponent_ax.axis("off")
    opponent_ax.imshow(McLachBotBadgeService().team_badge(league, team_image_names[1]))
    # Add the rounded bbox patch to the axes
    ax.add_patch(rounded_bbox)
