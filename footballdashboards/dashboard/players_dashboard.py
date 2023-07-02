from abc import abstractmethod
from footballdashboards.helpers.pitch_helpers import (
    draw_passes_on_axes,
    draw_pass_legend_on_axes,
    plot_positional_heatmap_on_pitch,
    draw_defensive_events_on_axes,
    draw_convex_hull_without_outliers_on_axes,
    draw_defensive_event_legend,
)
from footballdashboards.dashboard.dashboard import Dashboard
from dbconnect.connector import Connection
from footballdashboards.elements.headers import match_dashboard_header
import pandas as pd
from typing import Dict

from footballdashboards._types._custom_types import PlotReturnType
from mplsoccer import Pitch
from footballdashboards._types._dashboard_fields import ColorField
from footballdashboards.helpers.mplsoccer_helpers import make_grid
from footmav.data_definitions.whoscored.constants import EventType
from footballdashboards.helpers.data_helpers import extract_names_sorted_by_position
from footballdashboards.helpers.fonts import font_normal
from footmav.utils import whoscored_funcs as WF
from footballdashboards.helpers.formatters import length_based_name_formatter
import cmasher as cmr
from matplotlib.axes import Axes
import math
from footmav.utils import whoscored_funcs as wf
from footballdashboards.helpers.matplotlib import get_aspect
from urllib.request import urlopen
from PIL import Image


class MatchDashboard(Dashboard):
    GRID_PARAMETERS = {
        "title_height": 0.06,
        "figheight": 12,
        "grid_height": 0.85,
        "endnote_height": 0.06,
    }
    GRID_NROWS = 6
    GRID_NCOLS = 3
    linecolor = ColorField("Pitch line color", default="#000000")
    secondary_textcolor = ColorField("Secondary text color", default="#666666")

    def _required_data_columns(self) -> Dict[str, str]:
        return {}

    def _setup_pitch(self):
        pitch = Pitch(
            pitch_type="opta",
            pitch_color=self.facecolor,
            line_color=self.linecolor,
            linewidth=1,
        )
        return pitch

    def _setup_figure(self, pitch) -> PlotReturnType:

        fig, axes = make_grid(
            pitch,
            nrows=self.GRID_NROWS,
            ncols=self.GRID_NCOLS,
            axis=False,
            **self.GRID_PARAMETERS,
        )

        fig.set_facecolor(self.facecolor)
        return fig, axes

    def _draw_header(self, ax, data):
        non_carry = data.loc[data["event_type"] != EventType.Carry]
        # league = non_carry.iloc[0]["competition"]
        match_date = non_carry.iloc[0]["match_date"]
        league = non_carry.iloc[0]["decorated_league_name"]
        dec_team = non_carry.iloc[0]["decorated_team_name"]
        dec_opponent = non_carry.iloc[0]["decorated_opponent_name"]
        team = non_carry.iloc[0]["team"]
        opponent = non_carry.iloc[0]["opponent"]
        team_score = int(
            non_carry.iloc[0]["home_score"]
            if non_carry.iloc[0]["is_home_team"]
            else non_carry.iloc[0]["away_score"]
        )
        opponent_score = int(
            non_carry.iloc[0]["away_score"]
            if non_carry.iloc[0]["is_home_team"]
            else non_carry.iloc[0]["home_score"]
        )

        teams = [dec_team, dec_opponent]
        team_image_names = [team, opponent]
        scores = [team_score, opponent_score]
        home_away = "Home" if non_carry.iloc[0]["is_home_team"] else "Away"
        formations = [
            non_carry.iloc[0]["formation"],
            non_carry.iloc[0]["starting_opponent_formation"],
        ]

        match_dashboard_header(
            ax,
            match_date,
            league,
            teams,
            team_image_names,
            scores,
            formations,
            self.linecolor,
            self.facecolor,
            self.secondary_textcolor,
            home_away,
        )

    def _plot_watermark(self, ax: Axes):
        sub_ax = ax.inset_axes([1 - get_aspect(ax), 0, get_aspect(ax), 1], transform=ax.transAxes)
        sub_ax.axis("off")
        try:
            img = Image.open(urlopen(self.watermark))
            sub_ax.imshow(img, zorder=10)
        except:
            pass

    @abstractmethod
    def _plot_pitches(self, data, pitch, ax):
        pass

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        pitch = self._setup_pitch()
        fig, axes = self._setup_figure(pitch)
        self._draw_header(axes["title"], data)
        self._plot_pitches(data, pitch, axes)
        if self.watermark is not None:
            self._plot_watermark(axes["endnote"])
        return fig, axes


class PlayerMatchPassingDashboard(MatchDashboard):
    @property
    def datasource_name(self) -> str:
        return "match_passes"

    def _player_name_and_info(self, ax, player_data, text_color):
        player_data = player_data[player_data["event_type"] != EventType.Carry]
        player_name = player_data["player_name"].iloc[0]

        sub_on = player_data.loc[player_data["event_type"] == EventType.SubstitutionOn]
        sub_off = player_data.loc[player_data["event_type"] == EventType.SubstitutionOff]
        sub_str = ""
        if len(sub_on) > 0:
            sub_str = " ".join([sub_str, f"On: {sub_on['minute'].iloc[0]}"])
        if len(sub_off) > 0:
            sub_str = " ".join([sub_str, f"Off: {sub_off['minute'].iloc[0]}"])

        position_array = player_data.loc[
            (~player_data["position"].isin(["Substitute", "Error"])), "position"
        ]
        if position_array.shape[0] > 0:
            position = position_array.iloc[0]
        else:
            position = "Sub"
        number_array = player_data.loc[
            (~player_data["position"].isin(["Substitute", "Error"])),
            "shirt_number",
        ]
        if number_array.shape[0] > 0:
            number = number_array.iloc[0]
        else:
            number = ""

        player_name_display = length_based_name_formatter(player_name, 14)

        passes = player_data.loc[
            (player_data["event_type"] == EventType.Pass)
            & (~WF.col_has_qualifier(player_data, qualifier_code=107))
        ]
        n_tot = len(passes)
        completed_mask = passes["outcomeType"] == 1
        n_comp = len(passes[completed_mask])
        ax.text(
            0.03,
            0.97,
            f"{position} | {int(number)} | {player_name_display} | {n_comp}/{n_tot} ({n_comp/n_tot * 100 if n_tot > 0 else 0:.0f}%)",
            ha="left",
            va="bottom",
            fontsize=10,
            color=text_color,
            fontproperties=font_normal.prop,
            transform=ax.transAxes,
        )
        ax.text(
            0.03,
            0.04,
            sub_str,
            ha="left",
            va="bottom",
            fontsize=8,
            color=text_color,
            fontproperties=font_normal.prop,
            transform=ax.transAxes,
        )

    def _plot_pitches(self, data: pd.DataFrame, pitch: Pitch, axes: Dict[str, Axes]) -> None:
        names = extract_names_sorted_by_position(data)

        for i, name in enumerate(names):
            r_i = int(math.floor(i / 3))
            r_j = i % 3
            player_data = data[data["player_name"] == name].copy()
            draw_passes_on_axes(axes["pitch"][(r_i, r_j)], player_data, pitch)
            self._player_name_and_info(axes["pitch"][(r_i, r_j)], player_data, self.linecolor)

        plot_positional_heatmap_on_pitch(
            axes["pitch"][5][1],
            pitch,
            data,
            base_edge_color=self.linecolor,
            cmap=cmr.get_sub_cmap(cmr.amber_r, 0, 0.8),
        )
        axes["pitch"][5][1].text(
            0,
            107,
            f"Positional Pass Distribution",
            ha="left",
            va="center",
            fontsize=12,
            color=self.linecolor,
            fontproperties=font_normal.prop,
        )

        successful_pass_mask = (
            (data["event_type"] == EventType.Pass)
            & (data["outcomeType"] == 1)
            & (~wf.col_has_qualifier(data, qualifier_code=107))
        )
        pitch.kdeplot(
            data.loc[successful_pass_mask]["endX"],
            data.loc[successful_pass_mask]["endY"],
            ax=axes["pitch"][5][2],
            levels=50,
            shade=True,
            cmap=cmr.amber_r,
            thresh=0.1,
            alpha=0.8,
            zorder=0,
        )
        axes["pitch"][5][2].text(
            0,
            107,
            f"Passes Received Locations",
            ha="left",
            va="center",
            fontsize=12,
            color=self.linecolor,
            fontproperties=font_normal.prop,
        )
        draw_pass_legend_on_axes(axes["endnote"], self.facecolor, self.linecolor)


class PlayerMatchDefensiveDashboard(MatchDashboard):
    GRID_NROWS = 5
    markercolor = ColorField("Marker base color", default="#666666")

    @property
    def datasource_name(self) -> str:
        return "match_defensive_actions"

    def _player_name_and_info(self, ax, player_data, text_color):
        player_data = player_data[player_data["event_type"] != EventType.Carry]
        player_name = player_data["player_name"].iloc[0]

        sub_on = player_data.loc[player_data["event_type"] == EventType.SubstitutionOn]
        sub_off = player_data.loc[player_data["event_type"] == EventType.SubstitutionOff]
        sub_str = ""
        if len(sub_on) > 0:
            sub_str = " ".join([sub_str, f"On: {sub_on['minute'].iloc[0]}"])
        if len(sub_off) > 0:
            sub_str = " ".join([sub_str, f"Off: {sub_off['minute'].iloc[0]}"])

        position_array = player_data.loc[
            (~player_data["position"].isin(["Substitute", "Error"])), "position"
        ]
        if position_array.shape[0] > 0:
            position = position_array.iloc[0]
        else:
            position = "Sub"
        number_array = player_data.loc[
            (~player_data["position"].isin(["Substitute", "Error"])),
            "shirt_number",
        ]
        if number_array.shape[0] > 0:
            number = number_array.iloc[0]
        else:
            number = ""

        player_name_display = length_based_name_formatter(player_name, 14)
        ax.text(
            0.03,
            0.97,
            f"{position} | {number:.0f} | {player_name_display} ",
            ha="left",
            va="bottom",
            fontsize=10,
            color=text_color,
            fontproperties=font_normal.prop,
            transform=ax.transAxes,
        )
        ax.text(
            0.97,
            0.97,
            sub_str,
            ha="right",
            va="bottom",
            fontsize=10,
            color=text_color,
            fontproperties=font_normal.prop,
            transform=ax.transAxes,
        )

    def _plot_pitches(self, data, pitch, ax):
        names = extract_names_sorted_by_position(data, exclude_positions=["GK"])
        draw_defensive_event_legend(
            ax["endnote"],
            self.markercolor,
            self.linecolor,
            7,
            split=3,
            framealpha=0,
            edgecolor=self.facecolor,
            facecolor=self.facecolor,
            loc="upper left",
        )
        for i, name in enumerate(names):
            r_i = int(math.floor(i / self.GRID_NCOLS))
            r_j = i % self.GRID_NCOLS

            if name:
                draw_defensive_events_on_axes(
                    ax["pitch"][(r_i, r_j)],
                    data.loc[data["player_name"] == name],
                    pitch,
                    25,
                    self.markercolor,
                    self.linecolor,
                )
                draw_convex_hull_without_outliers_on_axes(
                    ax["pitch"][(r_i, r_j)],
                    data.loc[data["player_name"] == name],
                    pitch,
                    0.1,
                )
                self._player_name_and_info(
                    ax["pitch"][(r_i, r_j)],
                    data.loc[data["player_name"] == name],
                    self.linecolor,
                )
