from mplsoccer.pitch import VerticalPitch
from typing import Dict
import pandas as pd
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards.dashboard.dashboard import Dashboard
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Collection
from footballdashboards._types._dashboard_fields import FigSizeField, ColorField, DashboardField

from matplotlib.cm import ScalarMappable
import math
import cmasher as cmr
from matplotlib.colorbar import Colorbar
from matplotlib.colors import Normalize
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService
from footballdashboards.helpers.fonts import (
    font_bold,
    font_normal,
    font_varsity,
    font_italic,
    font_mono,
)
import colorsys
import matplotlib
import datetime as dt
from footmav.data_definitions.whoscored.constants import EventType
from footballdashboards.helpers.mclachbot_helpers import TeamColorHelper
from footmav.utils import whoscored_funcs as WF
from mpltable import Table
from footballdashboards.helpers import utils
from footballdashboards.helpers import formatters
from footballdashboards.helpers.data_helpers import lineup_card
from footballdashboards.helpers.mclachbot_helpers import get_ball_logo2
from matplotlib.patches import FancyBboxPatch


class PassNetworkDashboard(Dashboard):
    figsize = FigSizeField("Size of the dashboard", default=(10, 13))
    linecolor = ColorField("Color of the pitch lines", default="#000000")
    secondary_textcolor = ColorField("Secondary text color", default="#666666")
    min_pass_to_show = DashboardField("Minimum number of passes to show", default=5)
    MINSIZE = 200
    MAXSIZE = 1000
    MAX_TOUCH_QTY = 150
    MAX_PASS_SIZE = 15
    MAX_PASS_QTY = 50
    MAX_PASS_XT = 0.04

    def _get_touch_events(self, data):
        touch_events = [
            2,
            3,
            7,
            8,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            41,
            42,
            44,
            45,
            49,
            50,
            54,
            61,
            74,
        ]
        touch_events = [EventType(e) for e in touch_events] + [EventType.Carry]

        total_touches = data.loc[
            (data["event_type"].isin(touch_events))
            | ((data["event_type"] == EventType.Foul) & (data["outcomeType"] == 1))
            | (
                (
                    (data["event_type"] == EventType.Pass)
                    | (data["event_type"] == EventType.OffsidePass)
                )
                & ~(
                    WF.col_has_qualifier(data, qualifier_code=6)
                    | WF.col_has_qualifier(data, display_name="ThrowIn")
                )
            )  # excludes corners and throw-ins
        ].copy()
        return total_touches

    def _required_data_columns(self) -> Dict[str, str]:
        return {}

    @property
    def datasource_name(self) -> str:
        return "pass_network"

    def _hide_axes(self, axes: Collection[Axes]):
        for ax in axes:
            ax.axis("off")

    def _setup_plot(self):
        fig = Figure(figsize=self.figsize, facecolor=self.facecolor)
        fig.subplots_adjust(wspace=0, hspace=0)
        shape = [["header", "header"], ["sidebar", "pitch"], ["endnote", "endnote"]]
        axes = fig.subplot_mosaic(
            shape,
            height_ratios=[0.07, 0.9, 0.03],
            width_ratios=[0.2, 0.8],
        )
        self._hide_axes([axes[ax] for ax in axes if ax != "pitch"])

        return fig, axes

    def _setup_pitch(self, ax: Axes):
        pitch = VerticalPitch(
            pitch_type="opta",
            pitch_color=self.facecolor,
            line_color=self.linecolor,
            linewidth=1,
            line_alpha=0.5,
        )
        pitch.draw(ax=ax)
        logo_ax = pitch.inset_axes(6, 6 / 65 * 105, 11, 11 / 65 * 105, ax=ax, zorder=200)
        logo_ax.axis("off")
        logo_ax.imshow(get_ball_logo2())

        return pitch

    def _plot_touches(
        self, pitch: VerticalPitch, data: pd.DataFrame, ax: Axes, colors: Collection[str]
    ):
        data["size"] = data["count"].apply(
            lambda x: self.MINSIZE + (x / self.MAX_TOUCH_QTY) * (self.MAXSIZE - self.MINSIZE)
        )

        for i, row in data.iterrows():
            pitch.scatter(
                row["x"],
                row["y"],
                ax=ax,
                s=row["size"],
                color=colors[0],
                zorder=11,
                ec=self.linecolor,
                lw=1,
            )
            if i in ["RCDM", "LCDM", "RCAM", "LCAM"]:
                i = i.replace("C", "")
            pitch.annotate(
                i,
                (row["x"], row["y"]),
                ax=ax,
                color=colors[1],
                va="center",
                ha="center",
                size=8,
                zorder=11,
            )

    def _plot_pass_pairings(self, pitch: VerticalPitch, data: pd.DataFrame, ax: Axes):
        for i, row in data.iterrows():
            line = row
            lw = (
                self.MAX_PASS_SIZE
                if row["count"] > self.MAX_PASS_QTY
                else 0.5 + row["count"] / self.MAX_PASS_QTY * (self.MAX_PASS_SIZE - 0.5)
            )
            xt = max(min(row["xT"], self.MAX_PASS_XT), 0)
            cmap = cmr.get_sub_cmap("cool", 0.3, 1)
            color = xt / self.MAX_PASS_XT
            color = cmap(color)

            pitch.lines(
                line["x_from"],
                line["y_from"],
                line["x_to"],
                line["y_to"],
                ax=ax,
                lw=lw,
                zorder=1,
                color=color,
                alpha=0.8,
            )

    def _plot_score_box(self, data, ax, side):
        if side == "left":
            score_ax = ax.inset_axes((0.01, 0.0, get_aspect(ax), 1))
        else:
            score_ax = ax.inset_axes((0.99 - get_aspect(ax), 0.0, get_aspect(ax), 1))

        score_ax.set_xticks([])
        score_ax.set_yticks([])
        score_ax.spines["top"].set_visible(False)
        score_ax.spines["right"].set_visible(False)
        score_ax.spines["bottom"].set_visible(False)
        score_ax.spines["left"].set_visible(False)
        fc = self.facecolor
        if not fc.startswith("#"):
            fc = matplotlib.colors.cnames[fc]

        score_ax.set_facecolor(utils.get_complimentary_color(fc))
        non_carry = data.loc[data["event_type"] != EventType.Carry]
        if side == "left":
            score = (
                non_carry.iloc[0]["home_score"]
                if non_carry.iloc[0]["is_home_team"]
                else non_carry.iloc[0]["away_score"]
            )

        else:
            score = (
                non_carry.iloc[0]["away_score"]
                if non_carry.iloc[0]["is_home_team"]
                else non_carry.iloc[0]["home_score"]
            )
        score_ax.text(
            0.5,
            0.5,
            int(score),
            size=40,
            va="center_baseline",
            ha="center",
            color=self.linecolor,
            fontproperties=font_varsity.prop,
        )

    def _plot_title(self, data: pd.DataFrame, ax: Axes):
        non_carry = data.loc[data["event_type"] != EventType.Carry]
        # league = non_carry.iloc[0]["competition"]
        date = non_carry.iloc[0]["match_date"]
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

        # Create a rounded bounding box patch
        aspect = get_aspect(ax)
        ax.set_xlim(0, 1)
        y_max = 1 * aspect
        ax.set_ylim(0, y_max)
        rounded_bbox = FancyBboxPatch(
            (0.02, 0.02),
            0.96,
            y_max - 0.04,
            boxstyle="round,pad=0.02",
            ec=self.linecolor,
            fc=self.facecolor,
            zorder=100,
            transform=ax.transData,
            lw=2,
        )
        ax.text(
            x=0.5,
            y=y_max * 0.95,
            s=formatters.format_date(date),
            ha="center",
            va="top",
            size=10,
            fontproperties=font_normal.prop,
            color=self.secondary_textcolor,
            zorder=101,
        )
        ax.text(
            x=0.5,
            y=y_max * 0.05,
            s=f"{league} ({'Home' if non_carry.iloc[0]['is_home_team'] else 'Away'})",
            ha="center",
            va="bottom",
            size=10,
            fontproperties=font_normal.prop,
            color=self.secondary_textcolor,
            zorder=101,
        )
        ax.text(
            x=0.5,
            y=y_max * 0.5,
            s=f"{team_score} - {opponent_score}",
            ha="center",
            va="center",
            size=20,
            fontproperties=font_mono.prop,
            color=self.linecolor,
            zorder=101,
        )
        ax.text(
            x=0.11,
            y=y_max * 0.5,
            s=dec_team,
            ha="left",
            va="center",
            size=16,
            fontproperties=font_bold.prop,
            color=self.linecolor,
            zorder=101,
        )
        ax.text(
            x=0.89,
            y=y_max * 0.5,
            s=dec_opponent,
            ha="right",
            va="center",
            size=16,
            fontproperties=font_bold.prop,
            color=self.linecolor,
            zorder=101,
        )
        team_ax = ax.inset_axes((0.02, 0.04, aspect * 0.92, 0.92), zorder=200)
        team_ax.axis("off")
        team_ax.imshow(McLachBotBadgeService().team_badge(league, team))
        opponent_ax = ax.inset_axes(
            (1 - 0.02 - aspect * 0.92, 0.04, aspect * 0.92, 0.92), zorder=200
        )
        opponent_ax.axis("off")
        opponent_ax.imshow(McLachBotBadgeService().team_badge(league, opponent))
        # Add the rounded bbox patch to the axes
        ax.add_patch(rounded_bbox)

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        non_carry = data.loc[data["event_type"] != EventType.Carry]
        league = non_carry.iloc[0]["competition"]
        team = non_carry.iloc[0]["team"]
        formation = non_carry.iloc[0]["formation"]
        fig, axes = self._setup_plot()
        pitch = self._setup_pitch(axes["pitch"])
        average_pos = self._get_average_touch_positions_and_count(data, "position")
        pass_pairings = self._get_coordinates_for_pairings(
            self._get_pass_pairings(data, "position"), average_pos
        )
        colors = TeamColorHelper().get_colours(data["competition"].iloc[0], data["team"].iloc[0])
        minutes_range = (data["minute"].min(), data["minute"].max())
        pitch.annotate(
            f"Pass network spans\nminutes {minutes_range[0]} through {minutes_range[1]}",
            (99, 99),
            ax=axes["pitch"],
            color=self.linecolor,
            size=8,
            ha="left",
            va="top",
            fontproperties=font_italic.prop,
            alpha=0.5,
        )
        if data["filters"].iloc[0]:
            pitch.annotate(
                data.iloc[0]["filters"],
                (95, 99),
                ax=axes["pitch"],
                color=self.linecolor,
                size=8,
                ha="left",
                va="top",
                fontproperties=font_italic.prop,
                alpha=0.8,
            )

        self._plot_touches(pitch, average_pos, axes["pitch"], colors)
        self._plot_pass_pairings(pitch, pass_pairings, axes["pitch"])
        self._plot_title(data, axes["header"])
        self._plot_endnote(data, axes["endnote"])
        self._plot_sidebar(data, axes["sidebar"])
        small_pitch_ax = pitch.inset_axes(95, 5, 9, 9, ax=axes["pitch"], zorder=300)
        small_pitch = VerticalPitch(
            "opta",
            pitch_color=self.facecolor,
            line_color=self.linecolor,
            linewidth=1,
            line_alpha=0.5,
        )
        small_pitch.draw(small_pitch_ax)
        positions_dict = small_pitch.get_formation(formation)
        try:
            color = TeamColorHelper().get_colours(league, team)[0]
        except:
            color = "black"
        for position in positions_dict:
            x, y = positions_dict[position].x, positions_dict[position].y
            small_pitch.scatter(x, y, color=color, s=30, ax=small_pitch_ax)

        return fig, axes

    def _plot_lineups(self, data, ax):
        starters, subs = lineup_card(data)
        starters = starters.rename(columns={"No.": "#"})
        subs = subs.rename(columns={"No.": "#"})
        starters["#"] = starters["#"].astype(int)
        subs["#"] = subs["#"].astype(int)

        lineup_ax = ax.inset_axes([0.0, 0.09, 1.05, 0.18])
        subs_ax = ax.inset_axes([0.0, -0.0, 1.05, 0.09])
        Table(
            starters[["#", "Player", "Pos", "Off"]].reset_index(drop=True),
            lineup_ax,
            cell_options={"text_kwargs": {"fontsize": 7, "fontproperties": font_normal.prop}},
            col_widths={"#": 0.1, "Player": 0.6, "Pos": 0.15, "Off": 0.15},
            col_header_options={
                "text_kwargs": {
                    "fontsize": 8,
                },
                "alignment": "center",
            },
            border_options={
                "left": {"lw": 1, "color": "black"},
                "right": {"lw": 1, "color": "black"},
                "top": {"lw": 1, "color": "black"},
                "bottom": {"lw": 1, "color": "black"},
            },
            column_separator_kwargs={"lw": 1, "color": "black"},
            header_separator_kwargs={"lw": 1, "color": "black"},
        ).draw()
        Table(
            subs[["#", "Player", "Pos", "On"]].reset_index(drop=True),
            subs_ax,
            cell_options={"text_kwargs": {"fontsize": 7, "fontproperties": font_normal.prop}},
            col_widths={"#": 0.1, "Player": 0.6, "Pos": 0.15, "On": 0.15},
            col_header_options={
                "text_kwargs": {
                    "fontsize": 8,
                },
                "alignment": "center",
            },
            border_options={
                "left": {"lw": 1, "color": "black"},
                "right": {"lw": 1, "color": "black"},
                "top": {"lw": 1, "color": "black"},
                "bottom": {"lw": 1, "color": "black"},
            },
            column_separator_kwargs={"lw": 1, "color": "black"},
            header_separator_kwargs={"lw": 1, "color": "black"},
        ).draw()

    def _plot_sidebar(self, data, ax):
        self._plot_tables(data, ax)
        self._plot_lineups(data, ax)

    def _get_average_touch_positions_and_count(self, data: pd.DataFrame, aggregation_variable: str):
        data = self._get_touch_events(data)
        return (
            data.groupby(aggregation_variable)
            .agg({"x": "mean", "y": "mean", "id": "count"})
            .rename(columns={"id": "count"})
        )

    def _get_pass_pairings(self, data: pd.DataFrame, aggregation_variable: str):
        data = data[
            (data["event_type"] == EventType.Pass)
            & (data["outcomeType"] == 1)
            & (~data["pass_receiver_position"].isna())
            & (~data["position"].isna())
        ].copy()

        if aggregation_variable == "position":
            for i, r in data.iterrows():
                if r["position"] > r["pass_receiver_position"]:
                    data.loc[i, "A"] = r["position"]
                    data.loc[i, "B"] = r["pass_receiver_position"]
                else:
                    data.loc[i, "B"] = r["position"]
                    data.loc[i, "A"] = r["pass_receiver_position"]
            pass_pairings = (
                data.groupby(["A", "B"])
                .agg({"id": "count", "xT": "mean"})
                .rename(columns={"id": "count"})
            )

        pass_pairings = pass_pairings[pass_pairings["count"] >= self.min_pass_to_show]

        return pass_pairings

    def _get_coordinates_for_pairings(self, pass_pairings: pd.DataFrame, average_pos: pd.DataFrame):
        pass_pairings = pass_pairings.reset_index()
        pass_pairings = pass_pairings.merge(average_pos[["x", "y"]], left_on="A", right_index=True)
        pass_pairings = pass_pairings.merge(
            average_pos[["x", "y"]], left_on="B", right_index=True, suffixes=("_from", "_to")
        )

        return pass_pairings

    def _plot_endnote(self, data, ax):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        cbar_ax = ax.inset_axes((0.76, 0, 0.2, 0.5))
        cmap = cmap = cmr.get_sub_cmap("cool", 0.3, 1)
        norm = Normalize(vmin=0, vmax=self.MAX_PASS_XT)
        Colorbar(cbar_ax, ScalarMappable(norm=norm, cmap=cmap), orientation="horizontal")
        ax.text(0.76, 1.2, "xT per pass", size=10, ha="left", va="top", color=self.linecolor)
        instruction_text = (
            "Circle location indicates average position of player's actions"
            "\nCircle size indicates number of player's actions"
            "\nLine thickness indicates number of passes between players"
            "\nLine color indicates average xT of passes between players"
        )
        ax.text(
            0.25,
            1,
            instruction_text,
            ha="left",
            va="top",
            size=8,
            color=self.linecolor,
            fontproperties=font_italic.prop,
        )

    def _pass_attempted_table(self, data, ax):
        def _f(data):
            return (
                data.loc[data["event_type"].isin([EventType.Pass, EventType.BlockedPass])]
                .groupby(["shirt_number", "player_name"])
                .agg({"id": "count"})
                .rename(columns={"id": "value"})
                .sort_values("value", ascending=False)
                .head(3)
                .reset_index()
            )

        self._create_table_on_axis(data, _f, "Passes Attempted", ax)

    def _passes_completed_table(self, data, ax):
        def _f(data):
            return (
                data.loc[(data["event_type"].isin([EventType.Pass])) & (data["outcomeType"] == 1)]
                .groupby(["shirt_number", "player_name"])
                .agg({"id": "count"})
                .rename(columns={"id": "value"})
                .sort_values("value", ascending=False)
                .head(3)
                .reset_index()
            )

        self._create_table_on_axis(data, _f, "Passes Completed", ax)

    def _pass_completed_pct(self, data, ax):
        def _f(data):
            t = (
                data.loc[(data["event_type"].isin([EventType.Pass]))]
                .groupby(["shirt_number", "player_name"])
                .agg({"id": "count", "outcomeType": "sum"})
                .rename(columns={"id": "attempted", "outcomeType": "completed"})
            )
            t["value"] = t["completed"] / t["attempted"]
            t = t.loc[t["attempted"] >= 15]
            t = t.sort_values("value", ascending=False).head(3).reset_index()
            t["value"] = t["value"].apply(lambda x: f"{x*100:.0f}%")
            return t[["shirt_number", "player_name", "value"]]

        self._create_table_on_axis(
            data,
            _f,
            "Pct Passes Completed",
            ax,
            col_widths={"shirt_number": 0.15, "player_name": 0.65, "value": 0.2},
        )

    def _prog_passes_attempted(self, data, ax):
        def _f(data):
            prog_passes = data.loc[
                (data["event_type"] == EventType.Pass) & (WF.is_progressive(data))
            ]
            return (
                prog_passes.groupby(["shirt_number", "player_name"])
                .agg({"id": "count"})
                .rename(columns={"id": "value"})
                .sort_values("value", ascending=False)
                .head(3)
                .reset_index()
            )

        self._create_table_on_axis(data, _f, "Prog. Passes Attempted", ax)

    def _prog_passes_completed(self, data, ax):
        def _f(data):
            prog_passes = data.loc[
                (data["event_type"] == EventType.Pass)
                & (data["outcomeType"] == 1)
                & (WF.is_progressive(data))
            ]
            return (
                prog_passes.groupby(["shirt_number", "player_name"])
                .agg({"id": "count"})
                .rename(columns={"id": "value"})
                .sort_values("value", ascending=False)
                .head(3)
                .reset_index()
            )

        self._create_table_on_axis(data, _f, "Prog. Passes Completed", ax)

    def _prog_passes_received(self, data, ax):
        def _f(data):
            prog_passes = data.loc[
                (data["event_type"] == EventType.Pass)
                & (WF.is_progressive(data))
                & (data["outcomeType"] == 1)
                & (~data["pass_receiver_shirt_number"].isna())
            ]
            return (
                prog_passes.groupby(["pass_receiver_shirt_number", "pass_receiver"])
                .agg({"id": "count"})
                .reset_index()
                .rename(
                    columns={
                        "id": "value",
                        "pass_receiver_shirt_number": "shirt_number",
                        "pass_receiver": "player_name",
                    }
                )
                .sort_values("value", ascending=False)
                .reset_index(drop=True)
                .head(3)[["shirt_number", "player_name", "value"]]
            )

        self._create_table_on_axis(data, _f, "Prog. Passes Received", ax)

    def _plot_tables(self, data, ax: Axes):
        for i, f in enumerate(
            [
                self._pass_attempted_table,
                self._passes_completed_table,
                self._pass_completed_pct,
                self._prog_passes_attempted,
                self._prog_passes_completed,
                self._prog_passes_received,
            ]
        ):
            sub_x = ax.inset_axes((0, 0.88 - i * 0.12, 1.05, 0.10), zorder=10)

            f(data, sub_x)

    def _create_table_on_axis(self, data, data_f, title, ax, col_widths=None):
        col_widths = col_widths or {"shirt_number": 0.15, "player_name": 0.7, "value": 0.15}
        tbl_data = data_f(data)
        tbl_data["player_name"] = tbl_data["player_name"].apply(formatters.smart_name_formatter)

        tbl_data["shirt_number"] = tbl_data["shirt_number"].astype(int)

        Table(
            tbl_data,
            ax,
            table_title=title,
            show_column_names=False,
            col_widths=col_widths,
            title_options={
                "height": 0.3,
                "separator_kwargs": {"lw": 2, "color": "black"},
                "alignment": "left",
                "text_kwargs": {"fontproperties": font_bold.prop},
            },
            cell_options={"text_kwargs": {"fontproperties": font_normal.prop}},
        ).draw()
