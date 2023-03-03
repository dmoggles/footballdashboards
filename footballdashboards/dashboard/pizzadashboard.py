import pandas as pd
import numpy as np
from typing import Dict
from mplsoccer import add_image
from mplsoccer.py_pizza import PyPizza
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from footballdashboards.dashboard.dashboard import Dashboard
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards._types._dashboard_fields import ColorField, FigSizeField, DashboardField
from footballdashboards.helpers.fonts import font_normal, font_bold, font_italic
from footballdashboards.helpers.formatters import full_name_formatter
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService, get_ball_logo
from urllib.request import urlopen
from PIL import Image


class PizzaDashboard(Dashboard):
    FIG_SIZE_DEFAULT = (4 * 1.5, 5 * 1.5)
    STRAIGHT_LINE_COLOUR_DEFAULT = "#EBEBE9"
    SLICE_COLOUR_DEFAULT = "#1A78CF"
    fig_size = FigSizeField(description="Figure size", default=FIG_SIZE_DEFAULT)
    straight_line_color = ColorField(
        description="Straight line colour", default=STRAIGHT_LINE_COLOUR_DEFAULT
    )
    slice_color = ColorField(description="Slice colour", default=SLICE_COLOUR_DEFAULT)
    center_logo_url = DashboardField(description="URL of the center logo", default=None)

    def __init__(self, data_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_name = data_name

    @property
    def datasource_name(self) -> str:
        return self.data_name

    def _setup_figure(self):
        fig = Figure(figsize=self.fig_size, dpi=100, facecolor=self.facecolor)
        axes = {}
        axes["pizza"] = fig.add_axes(
            (0, 0.02, 1, 0.9), projection="polar", facecolor=self.facecolor, aspect="equal"
        )
        axes["title"] = fig.add_axes((0, 0.92, 1.0, 0.08), facecolor=self.facecolor)
        axes["title"].axis("off")
        axes["endnote"] = fig.add_axes((0, 0, 1, 0.02), facecolor=self.facecolor)
        axes["endnote"].axis("off")

        return fig, axes

    def _required_data_columns(self) -> Dict[str, str]:
        return {
            "Player": "Player Name",
            "Team": "Team name",
            "Competition": "Competitions included in the data",
            "Minutes": "Minutes played",
            "Season": "Which season this data is for",
            "Age": "Age of the player",
            "All Competitions": "All competitions included in the data to which the player was compared",
        }

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = self._setup_figure()
        self._plot_pizza(data, axes["pizza"])
        self._plot_title(data, axes["title"])
        self._plot_endnote(data, axes["endnote"])
        
        return fig, axes

    def _plot_title(self, data: pd.DataFrame, ax: Axes) -> Axes:
        ax.text(
            0.02,
            1.0,
            full_name_formatter(data["Player"].values[0]),
            ha="left",
            va="top",
            fontproperties=font_bold.prop,
            color=self.textcolor,
            fontsize=18,
        )
        ax.text(
            0.02,
            0.4,
            f"{data['Team'].values[0]} - {', '.join([c.strip() for c in data['Competition'].values[0].split(',')])}",
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=12,
        )
        ax.text(
            0.02,
            0.0,
            f"Season: {data['Season'].values[0]:.0f}",
            ha="left",
            va="bottom",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=12,
        )
        ax.text(
            0.75,
            1.0,
            f"Qual. Minutes: {data['Minutes'].values[0]:.0f}",
            ha="left",
            va="top",
            fontproperties=font_normal.prop,
            color=self.textcolor,
            fontsize=12,
        )
        if data["Age"].values[0] is not None:
            ax.text(
                0.75,
                0.65,
                f"Age: {data['Age'].values[0]:.0f}",
                ha="left",
                va="top",
                fontproperties=font_normal.prop,
                color=self.textcolor,
                fontsize=12,
            )
        template_name = {
            "CMPizza": "Midfielder",
            "CBPizza": "Centre Back",
            "FBPizza": "Full Back",
            "FWPizza": "Forward",
            "AMPizza": "Attacking Midfielder/Winger",
        }[self.datasource_name]
        ax.text(
            0.75,
            0.3,
            f"Template: {template_name}",
            ha="left",
            va="top",
            fontproperties=font_italic.prop,
            color=self.textcolor,
            fontsize=8,
        )
        if data["image_team"].values[0] is not None:
            try:
                badge_image = McLachBotBadgeService().team_badge(
                    data["image_league"].values[0], data["image_team"].values[0]
                )

                inset_ax = ax.inset_axes((-0.08, 0.2, get_aspect(ax) * 0.8, 0.8))
                inset_ax.axis("off")

                inset_ax.imshow(badge_image)
            except:
                pass
        return ax

    def _plot_endnote(self, data: pd.DataFrame, ax: Axes) -> Axes:
        ax.text(
            1.1,
            1,
            self.watermark,
            ha="right",
            va="top",
            fontproperties=font_italic.prop,
            color=self.textcolor,
            fontsize=8,
        )
        try:
            comparable = [c.strip() for c in data['All Competitions'].values[0].split(",")]

            ax.text(
                -0.1,
                1,
                "Compared to qualifying players in\n" + ", ".join(comparable),
                ha="left",
                va="top",
                fontproperties=font_italic.prop,
                color=self.textcolor,
                fontsize=8,
            )
        except:
            pass

        return ax

    def _plot_pizza(self, data: pd.DataFrame, ax: Axes) -> Axes:
        params = [
            c
            for c in data.columns
            if c
            not in [
                "Player",
                "Team",
                "Minutes",
                "Season",
                "Competition",
                "Age",
                "image_team",
                "image_league",
                "All Competitions"
            ]
        ]
        values = data[params].values[0]
        values = [int(v) for v in np.round(values * 100, decimals=0)]
        pypizza = PyPizza(
            params=params,
            background_color=self.facecolor,
            straight_line_color=self.straight_line_color,
            straight_line_lw=1,
            last_circle_lw=0,  # linewidth of last circle
            other_circle_lw=0,  # linewidth for other circles
            inner_circle_size=10,  # size of inner circle
        )
        pypizza.make_pizza(
            values,
            ax=ax,
            color_blank_space="same",
            slice_colors=[self.slice_color] * len(params),
            value_colors=[self.textcolor] * len(params),  # color for the value-text
            value_bck_colors=[self.slice_color] * len(params),  # color for the blank spaces
            blank_alpha=0.4,  # alpha for blank-space colors
            kwargs_slices=dict(
                edgecolor="#F2F2F2", zorder=2, linewidth=1
            ),  # values to be used when plotting slices
            kwargs_params=dict(
                color="#000000", fontsize=8, fontproperties=font_normal.prop, va="center"
            ),  # values to be used when adding parameter
            kwargs_values=dict(
                color="#000000",
                fontsize=8,
                fontproperties=font_normal.prop,
                zorder=3,
                bbox=dict(
                    edgecolor="#000000",
                    facecolor="cornflowerblue",
                    boxstyle="round,pad=0.2",
                    lw=1,
                ),
            ),  # values to be used when adding parameter-values
        )
        if self.center_logo_url:
            try:
                img = Image.open(urlopen(self.center_logo_url))
                ax_insert = ax.inset_axes((0.46, 0.46,0.08, 0.08), zorder=0)
                ax_insert.axis("off")

                ax_insert.imshow(
                    img,
                )
            except:
                pass

        return ax
