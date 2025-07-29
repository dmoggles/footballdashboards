from typing import Dict, Any, List
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from mplsoccer.pitch import Pitch
import datetime as dt
import numpy as np
from footballdashboards.helpers.fonts import font_normal, font_europa
from footballdashboards.helpers.mclachbot_helpers import (
    CachedPlayerImageHelper,
    McLachBotBadgeService,
    TeamColorHelper,
)
from footballdashboards.helpers.formatters import smartest_name_formatter_yet
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.dashboard.player_maps.helpers import calc_minutes
from matplotlib import colormaps
from scipy.ndimage import rotate
from footballdashboards.dashboard.player_maps.filter_applicator import apply_filters

def draw_title(
    config: Dict[str, Any], data: pd.DataFrame, fig: Figure, axes: Axes, pitch: Pitch, filters: List[str]
) -> Axes:

    def _draw_subheader(
        minutes: str,
        team_name: str,
        league_name: str,
        age: str,
        ax: Axes,
    ):
        tokens = league_name.split(",")
        if len(tokens) > 1:
            # strip champions league and europa league
            league_name = (
                next(t for t in tokens if "Champions League" not in t and "Europa League" not in t)
                + "*"
            )
        start_date = dt.datetime.strptime(config["start_date"], "%Y-%m-%d")
        end_date = dt.datetime.strptime(config["end_date"], "%Y-%m-%d")
        start_date_str = start_date.strftime("%d %b %Y")
        end_date_str = end_date.strftime("%d %b %Y")
        date_range = f"{start_date_str} - {end_date_str}"
        if age:
            full_str1 = f"{minutes:.0f} minutes | {age:.0f} years old"
        else:
            full_str1 = f"{minutes:.0f} minutes"
        full_str2 = f"{team_name} | {league_name.replace(',',', ')} | {date_range}"
        # if date_label:
        #    full_str2 = f"{full_str2} | {date_label}"
        ax.text(
            0.05,
            0.25,
            full_str1,
            fontproperties=font_normal.prop,
            fontsize=12,
            ha="left",
            va="bottom",
            zorder=10,
        )
        ax.text(
            0.05,
            0.1,
            full_str2,
            fontproperties=font_normal.prop,
            fontsize=12,
            ha="left",
            va="bottom",
            zorder=10,
        )

    def _plot_cutout(player_id: str, ax: Axes):
        aspect = get_aspect(ax)
        insert_ax = ax.inset_axes([1 - aspect - 0.04, 0, aspect, 1])
        insert_ax.axis("off")
        img = CachedPlayerImageHelper(None).get_player_image(player_id, ws=True)
        if img is None:
            return
        img = np.array(list(img.convert("RGBA").getdata())).reshape(img.height, img.width, 4)

        img = np.array(img)
        if not config.get("preserve_original_player_image", True):
            img = img[
                int(img.shape[0] * 0.0) : int(img.shape[0] * 0.5),
                int(img.shape[1] * 0.25) : int(img.shape[1] * 0.75),
            ]
        insert_ax.imshow(img, alpha=1)

    def _place_team_logo(team: str, league, ax: Axes, fig: Figure):
        img = McLachBotBadgeService().team_badge(league, team)
        img = np.array(list(img.convert("RGBA").getdata())).reshape(img.height, img.width, 4)
        rotated_img = rotate(img, 10, reshape=True)
        rotated_img = rotated_img[
            int(rotated_img.shape[0] / 5) : rotated_img.shape[0],
            int(rotated_img.shape[1] / 5) : rotated_img.shape[1],
        ]
        fig_aspect = fig.get_figheight() / fig.get_figwidth()
        img_size = 0.15
        ax = fig.add_axes([0, 1 - img_size, img_size * fig_aspect, img_size], zorder=0.1)
        ax.axis("off")
        ax.imshow(rotated_img, alpha=0.2)

    def _draw_name(player_name: str, ax: Axes):
        ax.text(
            0.06,
            0.6,
            smartest_name_formatter_yet(player_name),
            fontproperties=font_europa.prop,
            fontsize=38,
            ha="left",
            va="center",
            zorder=10,
        )

    def _draw_line(team_name: str, league_name: str, ax: Axes):
        color = TeamColorHelper().get_colours(league_name, team_name)
        if color is None or color[0] == "#bbbbbb":
            color = colormaps("coolwarm")(0.8)
        else:
            color = color[0]
        ax.plot([0.04, 0.96], [0.0, 0.0], lw=7, color=color, zorder=10)

    player_name = data["player_name"].iloc[0]
    team_name = data["team"].iloc[0]
    league_name = data["competition"].iloc[0]
    player_id = config["player_id"]
    minutes = calc_minutes(data)
    leagues = ", ".join(data["dln"].unique())
    age = data["age"].iloc[0]
    _draw_name(player_name, axes)
    _draw_line(team_name, league_name, axes)
    _place_team_logo(team_name, league_name, axes, fig)
    _plot_cutout(player_id, axes)
    _draw_subheader(minutes, data["dtn"].iloc[0], leagues, age if age else None, axes)
    return axes
