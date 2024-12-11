from typing import Dict
from footballdashboards.dashboard.dashboard import Dashboard
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards._types._dashboard_fields import FigSizeField, ColorField
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from mplsoccer import VerticalPitch
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService
from footballdashboards.helpers.fonts import font_normal, font_bold, font_mono
from matplotlib.patches import FancyBboxPatch
import datetime as dt
from mpltable import Table
from footballdashboards.helpers.mclachbot_helpers import get_ball_logo2
import pandas as pd
from footmav.data_definitions.whoscored.constants import EventType
from footmav.utils import whoscored_funcs as WF


class MatchShotDashboard(Dashboard):
    fig_scale = 8

    ENDNOTE_RATIO = 0.02
    TITLE_RATIO = 0.08

    second_textcolor = ColorField("secondary text color", "grey")
    goal_color = ColorField("goal color", "#136F63")
    shot_color = ColorField("shot color", "#3E2F5B")
    own_goal_color = ColorField("own goal color", "#F34213")

    @property
    def datasource_name(self) -> str:
        return "single_match_shots"

    def _required_data_columns(self) -> Dict[str, str]:
        return {}

    def _setup_pitch(self):
        fig = Figure(
            figsize=(
                self.fig_scale * 0.65,
                self.fig_scale * 1.05 / (1 - self.ENDNOTE_RATIO - self.TITLE_RATIO),
            )
        )
        fig.set_facecolor(self.facecolor)

        axes = fig.subplot_mosaic(
            [["title", "title"], ["pitch", "pitch"], ["endnote_l", "endnote_r"]],
            gridspec_kw={
                "height_ratios": [
                    self.TITLE_RATIO,
                    1 - self.ENDNOTE_RATIO - self.TITLE_RATIO,
                    self.ENDNOTE_RATIO,
                ]
            },
        )
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0, hspace=0)

        pitch = VerticalPitch(
            "opta", pitch_color=self.facecolor, linewidth=1, line_color=self.textcolor
        )
        pitch.draw(ax=axes["pitch"])
        #logo_ax = pitch.inset_axes(6, 6 / 65 * 105, 11, 11 / 65 * 105, ax=axes["pitch"], zorder=200)
        #logo_ax.axis("off")
        #logo_ax.imshow(get_ball_logo2())
        pitch.inset_image(6, 6 / 65 * 105, get_ball_logo2(), 15,  ax=axes["pitch"], zorder=200)
        return fig, axes, pitch

    def _plot_on_pitch_logos(
        self,
        ax: Axes,
        home_team_image_name: str,
        away_team_image_name: str,
        league_name: str,
        pitch: VerticalPitch,
    ):
        for i, img_name in zip([1, -1], [home_team_image_name, away_team_image_name]):
            #img_ax = pitch.inset_axes(50 + i * 15, 50, 20, 20 * get_aspect(ax), ax=ax, zorder=200)
            #img_ax.axis("off")
            #img_ax.imshow(McLachBotBadgeService().team_badge(league_name, img_name), zorder=200)
            pitch.inset_image(50 + i * 15, 50, McLachBotBadgeService().team_badge(league_name, img_name), 30, ax=ax, alpha=0.2)

    @staticmethod
    def _player_name_format(name: str) -> str:
        tokens = name.split(" ")
        if len(tokens) == 1:
            return name.upper()
        if len(tokens) == 2:
            return tokens[1].title()
        return f"{''.join([t[0].upper() for t in tokens])}"

    def _plot_table(self, table_df: pd.DataFrame, ax: Axes, pitch: VerticalPitch, i: int):
        n_rows = len(table_df)
        # inset ax
        x_offset = (2 + 8 / 5 * n_rows) * 0.8
        ax2 = pitch.inset_axes(50 + (x_offset + 0.5) * i, 50 + 34.5 * i, x_offset * 2, 30, ax=ax)
        ax2.axis("off")
        table_df = table_df.rename(
            columns={"player_name": "Player", "xG": "xG", "Shots": "Sh", "Goals": "Gls"}
        )
        table_df["Player"] = table_df["Player"].apply(lambda x: self._player_name_format(x))
        table_df["xG"] = table_df["xG"].apply(lambda x: f"{x:.2f}")
        table = Table(
            table_df,
            ax=ax2,
            col_widths={"Player": 0.5, "xG": 0.25, "Sh": 0.125, "Gls": 0.125},
            title_options=dict(
                text_kwargs=dict(color=self.textcolor, fontproperties=font_bold.prop, fontsize=9)
            ),
        )
        table.table_title = "Top Players"

        table.border_options.bottom = dict(lw=1, color=self.textcolor)
        table.border_options.left = dict(lw=1, color=self.textcolor)
        table.border_options.right = dict(lw=1, color=self.textcolor)
        table.border_options.top = dict(lw=1, color=self.textcolor)
        table.cell_options.alignment = "left"
        table.cell_options.padding = 0.01
        table.cell_options.text_kwargs = dict(
            color=self.textcolor, fontproperties=font_normal.prop, fontsize=8
        )
        table.column_separator_kwargs = dict(lw=1, color=self.second_textcolor)
        table.header_separator_kwargs = dict(lw=1, color=self.second_textcolor)
        table.col_header_options.extend_column_separator = True
        table.col_header_options.text_kwargs = dict(
            color=self.textcolor, fontproperties=font_bold.prop, fontsize=8
        )

        table.draw()

    def _plot_pitch_data(self, data: pd.DataFrame, ax: Axes, pitch: VerticalPitch):
        self._plot_shots(data, ax, pitch)
        events = data.loc[
            (data["event_type"] != EventType.Carry)
            & (~WF.col_has_qualifier(data, qualifier_code=28))
        ].copy()
        events["Goals"] = events["event_type"].apply(lambda x: 1 if x == EventType.Goal else 0)
        home_events = events.loc[
            (data["is_home_team"] == 1) & (events["event_type"] != EventType.Carry)
        ].copy()
        away_events = events.loc[
            (data["is_home_team"] == 0) & (events["event_type"] != EventType.Carry)
        ].copy()
        home_team_name = home_events["team"].tolist()[0]
        away_team_name = away_events["team"].tolist()[0]
        league_name = home_events["competition"].tolist()[0]
        home_events["xG"].fillna(0, inplace=True)
        away_events["xG"].fillna(0, inplace=True)
        home_table = (
            home_events.groupby("player_name")
            .agg({"xG": "sum", "id": "count", "Goals": "sum"})
            .rename(columns={"id": "Shots"})
            .sort_values("xG", ascending=False)
            .head(5)
            .reset_index()
        )
        away_table = (
            away_events.groupby("player_name")
            .agg({"xG": "sum", "id": "count", "Goals": "sum"})
            .rename(columns={"id": "Shots"})
            .sort_values("xG", ascending=False)
            .head(5)
            .reset_index()
        )
        self._plot_on_pitch_logos(ax, home_team_name, away_team_name, league_name, pitch)
        self._plot_table(home_table, ax, pitch, 1)
        self._plot_table(away_table, ax, pitch, -1)

    def _plot_shots(self, data: pd.DataFrame, ax: Axes, pitch: VerticalPitch):
        data["size"] = data["xG"].apply(lambda x: 40 + 500 * x)
        shots = data.loc[
            data["event_type"].isin(
                [EventType.ShotOnPost, EventType.MissedShots, EventType.SavedShot]
            )
        ].copy()
        goals = data.loc[
            (data["event_type"] == EventType.Goal)
            & (~WF.col_has_qualifier(data, qualifier_code=28))
        ].copy()
        own_goals = data.loc[
            (data["event_type"] == EventType.Goal) & (WF.col_has_qualifier(data, qualifier_code=28))
        ].copy()
        if len(shots) > 0:
            pitch.scatter(
                shots["x"],
                shots["y"],
                s=shots["size"],
                ax=ax,
                color=self.shot_color,
                zorder=2,
                alpha=0.5,
            )
        if len(goals) > 0:
            pitch.scatter(
                goals["x"],
                goals["y"],
                s=goals["size"],
                ax=ax,
                color=self.goal_color,
                zorder=3,
                alpha=0.8,
            )
        if len(own_goals) > 0:
            pitch.scatter(
                own_goals["x"],
                own_goals["y"],
                s=100,
                ax=ax,
                color=self.own_goal_color,
                zorder=3,
                alpha=0.8,
            )

    def _plot_title(self, data: pd.DataFrame, ax: Axes):
        ax.axis("off")
        events = data.loc[data["event_type"] != EventType.Carry].copy()
        home_events = events.loc[events["is_home_team"] == 1].copy()
        away_events = events.loc[events["is_home_team"] == 0].copy()
        date = data["match_date"].iloc[0]
        league = home_events["competition"].tolist()[0]
        decorated_league_name = events["decorated_league_name"].tolist()[0]
        home_team = home_events["team"].tolist()[0]
        away_team = away_events["team"].tolist()[0]
        decorated_home_team = home_events["decorated_team_name"].tolist()[0].replace(" Women", "")
        decorated_away_team = away_events["decorated_team_name"].tolist()[0].replace(" Women", "")
        home_score = events["home_score"].tolist()[0]
        away_score = events["away_score"].tolist()[0]

        ax.add_patch(
            FancyBboxPatch(
                (-0.05, 0),
                1.1,
                1,
                boxstyle="round,rounding_size=0.02,pad=0.",
                facecolor=self.facecolor,
                edgecolor=self.textcolor,
                linewidth=2,
                clip_on=False,
                mutation_aspect=10,
            )
        )
        ax.text(
            0.5,
            0.80,
            f'{date.strftime("%A, %B %d %Y")}',
            color=self.second_textcolor,
            va="center",
            ha="center",
            fontproperties=font_normal.prop,
            fontsize=14,
        )
        ax.text(
            0.5,
            0.5,
            f"{home_score:.0f} - {away_score:.0f}",
            color=self.textcolor,
            va="center",
            ha="center",
            fontproperties=font_mono.prop,
            fontsize=20,
        )
        max_team_length = max(len(decorated_home_team), len(decorated_away_team))
        fontsize = 16
        if max_team_length >= 17:
            fontsize = 15
        if max_team_length >= 18:
            fontsize = 14
        if max_team_length >= 19:
            fontsize = 13
        if max_team_length >= 21:
            fontsize = 12
        if max_team_length >= 22:
            fontsize = 11

        ax.text(
            0.09,
            0.5,
            f"{decorated_home_team}",
            color=self.textcolor,
            va="center",
            ha="left",
            fontproperties=font_normal.prop,
            fontsize=fontsize,
        )
        ax.text(
            0.91,
            0.5,
            f"{decorated_away_team}",
            color=self.textcolor,
            va="center",
            ha="right",
            fontproperties=font_normal.prop,
            fontsize=fontsize,
        )
        ax.text(
            0.5,
            0.20,
            decorated_league_name,
            color=self.second_textcolor,
            va="center",
            ha="center",
            fontproperties=font_normal.prop,
            fontsize=14,
        )
        home_img = McLachBotBadgeService().team_badge(league, home_team)
        away_img = McLachBotBadgeService().team_badge(league, away_team)

        ax2 = ax.inset_axes((-0.03, 0.105, get_aspect(ax) * 0.79, 0.79))
        ax2.imshow(home_img)
        ax2.axis("off")
        ax3 = ax.inset_axes((1.03 - get_aspect(ax) * 0.79, 0.105, get_aspect(ax) * 0.79, 0.79))
        ax3.imshow(away_img)
        ax3.axis("off")

    def _plot_left_legend(self, ax: Axes):
        ax.axis("off")
        legend_handles = [
            ax.scatter([], [], s=40, color=self.shot_color, alpha=0.5),
            ax.scatter([], [], s=40, color=self.goal_color, alpha=0.8),
            ax.scatter([], [], s=40, color=self.own_goal_color, alpha=0.8),
        ]
        legend_labels = ["Shot", "Goal", "Own Goal"]
        ax.legend(
            legend_handles,
            legend_labels,
            loc="center left",
            ncol=3,
            facecolor=self.facecolor,
            edgecolor=self.textcolor,
            fontsize=8,
        )

    def _plot_right_legend(self, ax: Axes):
        ax.axis("off")
        xGs = [0.05, 0.15, 0.25, 0.35]
        legend_handles = [
            ax.scatter([], [], s=40 + xg * 500, color=self.shot_color, alpha=0.5) for xg in xGs
        ]
        legend_labels = [f"xG = {xg:.2f}" for xg in xGs]
        ax.legend(
            legend_handles,
            legend_labels,
            loc="center right",
            ncol=2,
            facecolor=self.facecolor,
            edgecolor=self.textcolor,
            fontsize=8,
        )

    def _plot_endnote(self, ax_l, ax_r):
        self._plot_left_legend(ax_l)
        self._plot_right_legend(ax_r)

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes, pitch = self._setup_pitch()

        self._plot_pitch_data(data, axes["pitch"], pitch)
        self._plot_title(data, axes["title"])
        self._plot_endnote(axes["endnote_l"], axes["endnote_r"])

        return fig, axes
