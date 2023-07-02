from typing import Dict
import pandas as pd
from footballdashboards.dashboard.dashboard import Dashboard
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards._types._dashboard_fields import FigSizeField, ColorField, DashboardField
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from footballdashboards.helpers.fonts import font_normal, font_bold, font_italic
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService, get_ball_logo
from footballdashboards.helpers.matplotlib import get_aspect
import numpy as np
from urllib.request import urlopen
from PIL import Image


class RollingNPxGDashboard(Dashboard):
    FIG_SIZE_DEFAULT = (15, 16)

    fig_size = FigSizeField(description="Figure size", default=FIG_SIZE_DEFAULT)
    pos_color = ColorField(description="Positive color", default="blue")
    neg_color = ColorField(description="Negative color", default="red")
    for_npxg_color = ColorField(description="For npxg color", default="black")
    against_npxg_color = ColorField(description="Against npxg color", default="grey")
    textcolor = ColorField(description="Text color", default="black")
    secondary_textcolor = ColorField(description="Secondary text color", default="grey")
    watermark_image = DashboardField(description="Watermark image URL", default=None)

    @property
    def datasource_name(self) -> str:
        return "rolling_npxg"

    def _required_data_columns(self) -> Dict[str, str]:
        return {
            "date": "Date of the match",
            "opponent": "Opponent",
            "npxg": "Non-penalty expected goals for",
            "npxg_opp": "Non-penalty expected goals against",
            "round": "Round of the match",
            "season": "Season",
            "team": "Team name",
            "league": "League name",
            "rolling_window": "size of the rolling window",
            "normalized": "whether the npxg data is normalized for league average",
            "team_img": "name of the team to use in sportsdb service to retrieve team logo",
        }

    def _setup_figure(self):
        fig = Figure(figsize=self.fig_size, dpi=100, facecolor=self.facecolor)
        axes = fig.subplot_mosaic(
            [["title"], ["plot"], ["endnote"]], height_ratios=[0.08, 0.9, 0.02]
        )
        fig.subplots_adjust(wspace=0, hspace=0)
        for ax_name in ["title", "endnote"]:
            axes[ax_name].axis("off")
            axes[ax_name].set_facecolor(self.facecolor)
        axes["plot"].set_facecolor(self.facecolor)
        return fig, axes

    def _setup_main_axes(self, ax: Axes):
        ax.set_xlabel("Date", fontproperties=font_normal.prop, size=14)
        ax.set_ylabel("Non-penalty Expected Goals", fontproperties=font_normal.prop, size=14)
        ax.grid(alpha=0.1)

    def _adjust_scaling(self, ax, data, c_for, c_against):
        minimum_y = min(min(data[c_for]), min(data[c_against]))
        maximum_y = max(max(data[c_for]), max(data[c_against]))
        ax.set_ylim(minimum_y - 0.2, maximum_y + 0.2)
        ax.set_xlim(min(data["round"].values - 0.5), max(data["round"].values + 0.5))

    def _set_x_ticks(self, ax, data):
        ax.set_xticks(data["round"].values)
        ax.set_xticklabels(
            data["date"].apply(lambda x: x.strftime("%Y-%m-%d")).values,
            rotation=45,
            fontproperties=font_italic.prop,
            size=12,
        )

    def _set_opposition_images(self, ax, data):
        league = data["league"].iloc[0]
        x_size = ax.get_xlim()[1] - ax.get_xlim()[0]
        y_size = ax.get_ylim()[1] - ax.get_ylim()[0]
        for x_d, opp_name in zip(data["round"].values, data["opponent"]):
            ax_1 = ax.inset_axes(
                (x_d - 0.3, ax.get_ylim()[0] + 0.05, 0.6, 0.6 / (x_size) * y_size),
                transform=ax.transData,
            )
            try:
                ax_1.imshow(McLachBotBadgeService().team_badge(league, opp_name))
            except:
                ax_1.text(
                    0.5,
                    0.5,
                    "\n".join(opp_name.replace("_", " ").title()),
                    fontproperties=font_bold.prop,
                    size=8,
                    ha="center",
                    va="center",
                    color=self.textcolor,
                )
            ax_1.axis("off")

    def _plot_npxg(self, data, ax: Axes):
        team = data["team"].iloc[0]

        self._setup_main_axes(ax)
        c_for = "npxg"
        c_against = "npxg_opp"
        pos = np.array(data[c_for].values >= data[c_against])
        neg = np.array(data[c_for].values < data[c_against])
        ax.fill_between(
            data["round"].values,
            data[c_for],
            y2=data[c_against],
            where=pos,
            color=self.pos_color,
            alpha=0.5,
            interpolate=True,
        )
        ax.plot(
            data["round"].values,
            data[c_for],
            color=self.for_npxg_color,
            label=f"{team.replace('_',' ').title()} NPxG",
        )
        ax.fill_between(
            data["round"].values,
            data[c_for],
            y2=data[c_against],
            where=neg,
            color=self.neg_color,
            alpha=0.5,
            interpolate=True,
        )
        ax.plot(
            data["round"].values,
            data[c_against],
            color=self.against_npxg_color,
            label="Opponent NPxG",
        )

        self._adjust_scaling(ax, data, c_for, c_against)
        self._set_x_ticks(ax, data)
        self._set_opposition_images(ax, data)
        ax.legend(loc="upper left", prop=font_normal.prop, frameon=True)

    def _plot_title(self, data, ax: Axes):
        league = data["league"].iloc[0]
        season = data["season"].iloc[0]
        team = data["team"].iloc[0]
        team_img = data["team_img"].iloc[0]
        rolling_window = data["rolling_window"].iloc[0]
        normalized = data["normalized"].iloc[0]

        team_logo_axis = ax.inset_axes(
            (0.0, 0.1, 0.8 * get_aspect(ax), 0.8), transform=ax.transAxes
        )
        team_logo_axis.imshow(McLachBotBadgeService().team_badge(league, team_img))
        team_logo_axis.axis("off")

        league_logo_axis = ax.inset_axes(
            (1.0 - get_aspect(ax) * 0.8, 0.1, 0.8 * get_aspect(ax), 0.8), transform=ax.transAxes
        )
        league_logo_axis.imshow(McLachBotBadgeService().league_badge(league))
        league_logo_axis.axis("off")
        title = f"{team} - Rolling NPxG For and Against"
        ax.text(
            0.1,
            0.8,
            title,
            fontproperties=font_bold.prop,
            size=20,
            ha="left",
            va="top",
            transform=ax.transAxes,
            color=self.textcolor,
        )
        subtitle = f"{season} season - {rolling_window} game rolling window"
        ax.text(
            0.1,
            0.2,
            subtitle,
            fontproperties=font_italic.prop,
            size=12,
            ha="left",
            va="bottom",
            transform=ax.transAxes,
            color=self.textcolor,
        )
        if normalized:
            ax.text(
                0.9,
                0.2,
                "(NPxG normalized for opposition quality.)",
                size=10,
                ha="right",
                va="bottom",
                transform=ax.transAxes,
                fontproperties=font_italic.prop,
                color=self.secondary_textcolor,
            )

    def _add_watermark(self, ax: Axes):
        dislocate_text = 0.0
        if self.watermark_image:
            try:

                ratio = ax.transAxes.transform((1, 1))[1] / ax.transAxes.transform((1, 1))[0]

                image = Image.open(urlopen(self.watermark_image))
                water_mark_ax = ax.inset_axes(
                    (1.0 - 0.05 * ratio - 0.005, 1 - 0.055, 0.05 * ratio, 0.05),
                    transform=ax.transAxes,
                )

                water_mark_ax.imshow(image)
                water_mark_ax.axis("off")
                dislocate_text = 0.05
            except:
                pass
        if self.watermark:
            ax.text(
                0.99 - dislocate_text,
                0.985,
                self.watermark,
                size=8,
                ha="right",
                va="top",
                transform=ax.transAxes,
                fontproperties=font_italic.prop,
                color=self.secondary_textcolor,
            )

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = self._setup_figure()

        self._plot_npxg(data, axes["plot"])
        self._plot_title(data, axes["title"])
        self._add_watermark(axes["plot"])

        return fig, axes
