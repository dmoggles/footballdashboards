from mplsoccer.dimensions import opta_dims
from typing import Tuple, List, Dict
import numpy as np
import pandas as pd
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards._types._dashboard_fields import ColorField, DashboardField
from footballdashboards.dashboard.dashboard import Dashboard
from footmav.utils.whoscored_funcs import in_rectangle
import matplotlib.cm as cm
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from footballdashboards.helpers.fonts import font_normal, font_bold, font_italic
from footballdashboards.helpers.formatters import full_name_formatter, simplified_opta_position
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService, get_image
from footballdashboards.helpers.matplotlib import get_aspect
from matplotlib.colorbar import Colorbar
from highlight_text import ax_text
import cmasher as cmr
from mplsoccer.pitch import VerticalPitch
from matplotlib.figure import Figure
from matplotlib.axes import Axes


class FinishingDashboard(Dashboard):
    linecolor = ColorField("Line color", "black")
    highlight_text_color = ColorField("Highlight text color", "#127475")
    badge_url = DashboardField("Badge URL", "http://www.mclachbot.com/site/img/ball_logo.png")

    RECTANGLES = {
        "left_near_box": (
            (100, opta_dims().penalty_area_top),
            (
                100 - (100 - opta_dims().penalty_area_right) / 2,
                opta_dims().penalty_area_top - opta_dims().penalty_area_width / 3,
            ),
        ),
        "left_far_box": (
            (100 - (100 - opta_dims().penalty_area_right) / 2, opta_dims().penalty_area_top),
            (
                opta_dims().penalty_area_right,
                opta_dims().penalty_area_top - opta_dims().penalty_area_width / 3,
            ),
        ),
        "center_near_box": (
            (100, opta_dims().penalty_area_top - opta_dims().penalty_area_width / 3),
            (
                100 - (100 - opta_dims().penalty_area_right) / 2,
                opta_dims().penalty_area_top - opta_dims().penalty_area_width * 2 / 3,
            ),
        ),
        "center_far_box": (
            (
                100 - (100 - opta_dims().penalty_area_right) / 2,
                opta_dims().penalty_area_top - opta_dims().penalty_area_width / 3,
            ),
            (
                opta_dims().penalty_area_right,
                opta_dims().penalty_area_top - opta_dims().penalty_area_width * 2 / 3,
            ),
        ),
        "right_near_box": (
            (100, opta_dims().penalty_area_top - opta_dims().penalty_area_width * 2 / 3),
            (100 - (100 - opta_dims().penalty_area_right) / 2, opta_dims().penalty_area_bottom),
        ),
        "right_far_box": (
            (
                100 - (100 - opta_dims().penalty_area_right) / 2,
                opta_dims().penalty_area_top - opta_dims().penalty_area_width * 2 / 3,
            ),
            (opta_dims().penalty_area_right, opta_dims().penalty_area_bottom),
        ),
        "wide_left": ((100, 100), (75, opta_dims().penalty_area_top)),
        "wide_right": ((100, opta_dims().penalty_area_bottom), (75, 0)),
        "outside_box": (
            (opta_dims().penalty_area_right, opta_dims().penalty_area_top),
            (75, opta_dims().penalty_area_bottom),
        ),
        "far": ((75, 100), (0, 0)),
    }

    @staticmethod
    def _corners_to_vertices(
        corners: Tuple[Tuple[float, float], Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        return np.array(
            [
                list(corners[0]),
                [corners[0][0], corners[1][1]],
                list(corners[1]),
                [corners[1][0], corners[0][1]],
            ]
        )

    @staticmethod
    def _in_rectange(r: pd.Series):
        try:
            return next(
                key
                for key, value in FinishingDashboard.RECTANGLES.items()
                if in_rectangle(r["x"], r["y"], value[0][0], value[0][1], value[1][0], value[1][1])
            )
        except StopIteration:
            return ""

    @staticmethod
    def _rescale_colormap(data, vmin, vmax, cmap_name):
        norm = lambda x: (min(max(x, vmin), vmax) - vmin) / (vmax - vmin)
        cmap = cm.get_cmap(cmap_name)
        return [cmap(norm(value)) for value in data]

    @property
    def datasource_name(self) -> str:
        return "player_shot_data"

    def _required_data_columns(self) -> Dict[str, str]:
        return {}

    def _setup_fig(self) -> Figure:
        fig = Figure(figsize=(8, 8 * 0.6), dpi=300)
        fig.set_facecolor(self.facecolor)
        axes = fig.subplot_mosaic(
            [
                ["header", "header"],
                ["pitch", "data_r"],
                ["pitch_legend", "data_r"],
                ["endnote", "endnote"],
            ],
            height_ratios=[0.1, 0.35, 0.1, 0.05],
            width_ratios=[0.6, 0.4],
        )
        fig.subplots_adjust(wspace=0, hspace=0)
        for ax in axes.values():
            ax.axis("off")
        pitch = VerticalPitch(
            pitch_type="opta",
            pitch_color=self.facecolor,
            line_color=self.linecolor,
            half=True,
            linewidth=1,
        )
        pitch.draw(ax=axes["pitch"])
        axes["pitch"].set_ylim((70, 104))
        return fig, axes, pitch

    def _draw_pitch_rectangles(self, pitch: VerticalPitch, ax: Axes):
        for rectangle in self.RECTANGLES.values():
            pitch.polygon(
                [self._corners_to_vertices(rectangle)],
                ax=ax,
                ec="grey",
                zorder=1,
                lw=1,
                fill=False,
                alpha=0.2,
            )

    def _plot_agg_shots(
        self, data: pd.DataFrame, pitch: VerticalPitch, ax: Axes, fig: Figure
    ) -> None:
        data["rectange"] = data.apply(self._in_rectange, axis=1)
        agg_data = (
            data.groupby("rectange").agg({"xg": "sum", "meta_id": "count", "is_goal": "sum"})
            / data["minutes"].iloc[0]
            * 90
        )
        agg_data = agg_data.rename(columns={"meta_id": "shots", "is_goal": "goals"})
        agg_data["goals_minus_xg_per_shot"] = (agg_data["goals"] - agg_data["xg"]) / agg_data[
            "shots"
        ]
        agg_data["x"] = agg_data.index.map(
            lambda x: (self.RECTANGLES[x][0][0] + self.RECTANGLES[x][1][0]) / 2
            if x != "far"
            else 72.5
        )
        agg_data["y"] = agg_data.index.map(
            lambda x: (self.RECTANGLES[x][0][1] + self.RECTANGLES[x][1][1]) / 2
        )
        # agg_data['color']=self._rescale_colormap(agg_data['goals_minus_xg_per_shot'], vmin=-0.15, vmax=0.15, cmap_name='RdYlGn')

        pitch.scatter(
            x=agg_data["x"],
            y=agg_data["y"],
            s=agg_data["shots"] * 500,
            c=agg_data["goals_minus_xg_per_shot"],
            ax=ax,
            zorder=2,
            ec="black",
            lw=1,
            cmap="RdYlGn",
            vmin=-0.15,
            vmax=0.15,
        )
        pitch.annotate(
            "Shot Distribution",
            (104, 50),
            va="top",
            ha="center",
            ax=ax,
            fontproperties=font_bold.prop,
            fontsize=12,
        )

    def _plot_size_legend(self, pitch: VerticalPitch, ax: Axes, fig: Figure):
        dpi_factor = fig.get_dpi() / 100
        values = [0.25, 0.75, 1.25]
        lines = [
            ax.plot(
                [],
                [],
                "o",
                markersize=np.sqrt(value * 500),
                color=self.facecolor,
                markeredgecolor=self.linecolor,
                lw=1,
            )[0]
            for value in values
        ]

        leg = ax.legend(
            lines,
            values,
            ncol=3,
            frameon=False,
            fontsize=8,
            handlelength=1,
            loc="lower left",
            bbox_to_anchor=(0.5, 0.68),
            handletextpad=0,
            title="Shots/90",
        )
        title = leg.get_title()
        title.set_fontsize(10)
        title.set_fontproperties = font_normal.prop

        title.set_position((0, -62 * dpi_factor))
        for t in leg.get_texts():
            t.set_fontproperties(font_normal.prop)
            t.set_fontsize(8)
            t.set_ha("center")
            t.set_x(-15 * dpi_factor)
            t.set_y(-27 * dpi_factor)

    def _plot_legends(self, pitch: VerticalPitch, ax: Axes, fig: Figure) -> None:
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        cb_axis = ax.inset_axes([0.1, 0.7, 0.3, 0.3])
        cb = Colorbar(
            cb_axis,
            ScalarMappable(norm=Normalize(vmin=-0.15, vmax=0.15), cmap="RdYlGn"),
            orientation="horizontal",
        )
        cb.set_label("NPxG+ per Shot", fontproperties=font_normal.prop)
        cb.set_ticks([-0.15, -0.075, 0, 0.075, 0.15])
        cb.set_ticklabels(
            [f"{t:.2f}" for t in cb.get_ticks()], fontproperties=font_normal.prop, fontsize=8
        )

        self._plot_size_legend(pitch, ax, fig)

    def _plot_header(self, data: pd.DataFrame, ax: Axes) -> None:
        ax.axis("off")
        ax.text(
            0.12,
            0.9,
            full_name_formatter(data["player_name"].values[0]),
            ha="left",
            va="top",
            fontproperties=font_bold.prop,
            color=self.textcolor,
            fontsize=18,
        )
        ax.text(
            0.12,
            0.3,
            f"{data['decorated_team_name'].values[0]} - {', '.join([c.strip() for c in data['decorated_league_name'].values[0].split(',')])}",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=12,
        )
        ax.text(
            0.75,
            0.5,
            f"Season: {data['season'].values[0]}",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=12,
        )
        ax.text(
            0.75,
            1.0,
            f"Minutes: {data['minutes'].values[0]:.0f}",
            ha="left",
            va="top",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=12,
        )
        data["simplified_position"] = data["position"].apply(simplified_opta_position)
        value_counts = data["simplified_position"].value_counts()
        positions_to_display = value_counts.index[:3].tolist()
        ax.text(
            0.75,
            0,
            f"Positions: {', '.join([p.strip() for p in positions_to_display])}",
            ha="left",
            va="bottom",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=10,
        )

        badge_image = McLachBotBadgeService().team_badge(
            data["competition"].values[0], data["team"].values[0]
        )

        inset_ax = ax.inset_axes((0, 0.0, get_aspect(ax), 1))
        inset_ax.axis("off")

        inset_ax.imshow(badge_image)

    def _plot_side_data_panel(self, data: pd.DataFrame, ax: Axes) -> None:
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        shots = len(data)
        goals = data["is_goal"].sum()
        conversion_rate = data["is_goal"].sum() / len(data)
        npxg = data["xg"].sum()
        npxg_per_shot = data["xg"].sum() / len(data)

        right_footed_shots = data["right_foot"].sum()
        right_footed_goals = (data["right_foot"] * data["is_goal"]).sum()
        left_footed_shots = data["left_foot"].sum()
        left_footed_goals = (data["left_foot"] * data["is_goal"]).sum()
        headed_shots = data["header"].sum()
        headed_goals = (data["header"] * data["is_goal"]).sum()

        npxg_plus_per_shot = (data["is_goal"] - data["xg"]).sum() / len(data)
        touches_in_box_p90 = data["box_touches"].iloc[0] / data["minutes"].iloc[0] * 90
        shot_to_touch_ratio = len(data) / data["box_touches"].iloc[0]
        ax.text(
            0,
            0.88,
            "Player Profile",
            ha="left",
            va="top",
            fontproperties=font_bold.prop,
            color=self.textcolor,
            fontsize=12,
        )
        ax_text(
            0,
            0.78,
            f"<{shots:.0f}> Shots",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax_text(
            0.5,
            0.78,
            f"<{goals:.0f}> Goals",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax.hlines(0.75, 0, 0.8, color=self.textcolor, linewidth=0.5, linestyles="dashed")
        ax_text(
            0,
            0.72,
            f"<{conversion_rate:.0%}> Conversion Rate",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax_text(
            0.5,
            0.72,
            f"<{npxg:.1f}> NPxG",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax.hlines(0.69, 0, 0.8, color=self.textcolor, linewidth=0.5, linestyles="dashed")
        ax_text(
            0,
            0.66,
            f"<{right_footed_shots:.0f}> Right Foot Shots",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax_text(
            0.5,
            0.66,
            f"<{right_footed_goals:.0f}> Right Foot Goals",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax.hlines(0.63, 0, 0.8, color=self.textcolor, linewidth=0.5, linestyles="dashed")
        ax_text(
            0,
            0.60,
            f"<{left_footed_shots:.0f}> Left Foot Shots",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax_text(
            0.5,
            0.60,
            f"<{left_footed_goals:.0f}> Left Foot Goals",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax.hlines(0.57, 0, 0.8, color=self.textcolor, linewidth=0.5, linestyles="dashed")
        ax_text(
            0,
            0.54,
            f"<{headed_shots:.0f}> Headed Shots",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax_text(
            0.5,
            0.54,
            f"<{headed_goals:.0f}> Headed Goals",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax.hlines(0.51, 0, 0.8, color=self.textcolor, linewidth=0.5, linestyles="dashed")
        ax_text(
            0,
            0.48,
            f"<{touches_in_box_p90:.2f}> Touches in Box p90",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax.hlines(0.45, 0, 0.8, color=self.textcolor, linewidth=0.5, linestyles="dashed")
        ax_text(
            0,
            0.42,
            f"<{shot_to_touch_ratio:.2f}> Shot to Touch Ratio",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax.hlines(0.39, 0, 0.8, color=self.textcolor, linewidth=0.5, linestyles="dashed")
        ax_text(
            0,
            0.36,
            f"<{npxg_plus_per_shot:.2f}> NPxG+ per Shot",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=8,
            ax=ax,
            highlight_textprops=[{"color": self.highlight_text_color}],
        )
        ax.text(
            0,
            0.33,
            "Forecast NPxG+ per Shot Range",
            ha="left",
            va="top",
            fontproperties=font_bold.prop,
            color=self.textcolor,
            fontsize=8,
        )
        forecast_ax = ax.inset_axes((0, 0.24, 0.8, 0.03))

        min_forecasted_npxg_plus_per_shot = (
            conversion_rate
            - 1.96 * np.sqrt(conversion_rate * (1 - conversion_rate) / shots)
            - npxg_per_shot
        )
        max_forecasted_npxg_plus_per_shot = (
            conversion_rate
            + 1.96 * np.sqrt(conversion_rate * (1 - conversion_rate) / shots)
            - npxg_per_shot
        )
        bound_min_forecasted_npxg_plus_per_shot = min(
            max(min_forecasted_npxg_plus_per_shot, -0.15), 0.15
        )
        bound_max_forecasted_npxg_plus_per_shot = min(
            max(max_forecasted_npxg_plus_per_shot, -0.15), 0.15
        )
        cmap_start = (bound_min_forecasted_npxg_plus_per_shot + 0.15) / 0.3
        cmap_end = (bound_max_forecasted_npxg_plus_per_shot + 0.15) / 0.3
        cmap = cmr.get_sub_cmap("RdYlGn", cmap_start, cmap_end)
        colorbar = Colorbar(
            forecast_ax,
            ScalarMappable(
                norm=Normalize(
                    vmin=bound_min_forecasted_npxg_plus_per_shot,
                    vmax=bound_max_forecasted_npxg_plus_per_shot,
                ),
                cmap=cmap,
            ),
            orientation="horizontal",
        )
        colorbar.set_ticks(
            [bound_min_forecasted_npxg_plus_per_shot, bound_max_forecasted_npxg_plus_per_shot]
        )
        colorbar.set_ticklabels(
            [
                f"{min_forecasted_npxg_plus_per_shot:.2f}",
                f"{max_forecasted_npxg_plus_per_shot:.2f}",
            ],
            fontproperties=font_normal.prop,
            color=self.highlight_text_color,
            fontsize=8,
        )

    def _plot_endnote(self, ax: Axes) -> None:
        height = 2.0
        width = 2.0 * get_aspect(ax)
        logo_ax = ax.inset_axes((1 - width, 0, width, height))
        logo_ax.axis("off")

        # logo_ax.set_xlim(0, 1)
        # logo_ax.set_ylim(0, 1)
        logo_ax.imshow(get_image(self.badge_url))
        text = (
            "NPxG+ is defined as the difference between goals scored and non-penalty expected goals (NPxG)\n"
            r"Forecast NPxG+/Shot is calculated using a binomial dist 95% confidence interval, based on this season's sample."
        )
        ax.text(
            0.02, 0.5, text, ha="left", va="center", fontproperties=font_italic.prop, fontsize=8
        )

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes, pitch = self._setup_fig()
        # self._draw_pitch_rectangles(pitch, axes['pitch'])
        self._plot_agg_shots(data, pitch, axes["pitch"], fig)
        self._plot_legends(pitch, axes["pitch_legend"], fig)
        self._plot_side_data_panel(data, axes["data_r"])
        self._plot_header(data, axes["header"])
        self._plot_endnote(axes["endnote"])

        return fig, axes
