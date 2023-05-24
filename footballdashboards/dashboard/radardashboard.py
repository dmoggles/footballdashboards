from typing import Dict, List, Sequence
import pandas as pd
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards.dashboard.dashboard import Dashboard
from footballdashboards._types._dashboard_fields import (
    ColorField,
    FigSizeField,
    DashboardField,
    is_color_like,
)
from footballdashboards.helpers.fonts import font_normal, font_bold, font_italic
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from mplsoccer import Radar
from urllib.request import urlopen
from PIL import Image
import numpy as np
from footballdashboards.helpers.formatters import full_name_formatter
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService


class ColorListField(DashboardField):
    """
    Descriptor for color field.

    Validates that the color is in fact a valid matplotlib color
    """

    def _set_validate(self, value):
        assert isinstance(value, Sequence), f"{value} is not a valid sequence"
        for v in value:
            if not is_color_like(v):
                raise ValueError(f"{v} is not a valid color")
        return value


class RadarDashboard(Dashboard):
    FIG_SIZE_DEFAULT = (4 * 1.5, 5 * 1.5)
    STRAIGHT_LINE_COLOUR_DEFAULT = "#888888"
    SLICE_COLORMAP = "coolwarm_r"
    fig_size = FigSizeField(description="Figure size", default=FIG_SIZE_DEFAULT)
    radar_colors = ColorListField(description="Colors of radars drawn", default=["blue", "red"])
    circle_line_color = ColorField(
        description="circle line colour", default=STRAIGHT_LINE_COLOUR_DEFAULT
    )
    text_color = ColorField(description="Text colour", default="black")
    center_logo_url = DashboardField(description="URL of the center logo", default=None)

    def __init__(self, data_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_name = data_name

    @property
    def datasource_name(self) -> str:
        return self.data_name

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

    def _setup_figure(self):
        fig = Figure(figsize=self.fig_size, dpi=100, facecolor=self.facecolor)
        axes = {}
        axes["radar"] = fig.add_axes((0, 0.02, 1, 0.9), facecolor=self.facecolor, aspect="equal")
        axes["title"] = fig.add_axes((0, 0.92, 1.0, 0.08), facecolor=self.facecolor)
        axes["title"].axis("off")
        axes["endnote"] = fig.add_axes((0, 0, 1, 0.02), facecolor=self.facecolor)
        axes["endnote"].axis("off")

        return fig, axes

    def _get_param_names(self, data: pd.DataFrame) -> List[str]:
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
                "All Competitions",
                "Template Name",
            ]
            and "__value" not in c
        ]
        return params

    def _plot_header(self, ax: Axes, data: pd.DataFrame):
        player_1_name = data["Player"].iloc[0]
        player_2_name = data["Player"].iloc[1]
        team_1_name = data["Team"].iloc[0]
        team_2_name = data["Team"].iloc[1]
        competition_1 = next(
            c
            for c in data["Competition"].iloc[0].split(",")
            if c not in ["Champions League", "Europa League"]
        )
        competition_2 = next(
            c
            for c in data["Competition"].iloc[1].split(",")
            if c not in ["Champions League", "Europa League"]
        )
        season_1 = data["Season"].iloc[0]
        season_2 = data["Season"].iloc[1]
        image_name_1 = data["image_team"].iloc[0]
        image_name_2 = data["image_team"].iloc[1]
        image_league_1 = data["image_league"].iloc[0]
        image_league_2 = data["image_league"].iloc[1]
        age_1 = data["Age"].iloc[0]
        age_2 = data["Age"].iloc[1]
        minutes_1 = data["Minutes"].iloc[0]
        minutes_2 = data["Minutes"].iloc[1]

        ax_left_inset = ax.inset_axes([0, 0, get_aspect(ax), 1])
        ax_left_inset.axis("off")
        ax_left_inset.imshow(
            McLachBotBadgeService().team_badge(image_league_1, image_name_1),
        )
        ax_right_inset = ax.inset_axes([1 - get_aspect(ax), 0, get_aspect(ax), 1])
        ax_right_inset.axis("off")
        ax_right_inset.imshow(
            McLachBotBadgeService().team_badge(image_league_2, image_name_2),
        )
        ax.text(
            0.5,
            0.7,
            "VS",
            ha="center",
            va="center",
            color=self.text_color,
            fontsize=16,
            fontproperties=font_bold.prop,
        )
        template_name = data["Template Name"].iloc[0]
        ax.text(
            0.5,
            0.1,
            f"Template:\n{template_name}",
            ha="center",
            va="bottom",
            fontproperties=font_italic.prop,
            color=self.textcolor,
            fontsize=8,
        )
        ax.text(
            0.01 + get_aspect(ax),
            1.0,
            full_name_formatter(player_1_name),
            ha="left",
            va="top",
            color=self.radar_colors[0],
            fontsize=16,
            fontproperties=font_bold.prop,
        )

        ax.text(
            0.99 - get_aspect(ax),
            1.0,
            full_name_formatter(player_2_name),
            ha="right",
            va="top",
            color=self.radar_colors[1],
            fontsize=16,
            fontproperties=font_bold.prop,
        )
        ax.text(
            0.01 + get_aspect(ax),
            0.5,
            f"{competition_1} - {season_1}",
            ha="left",
            va="center",
            color=self.text_color,
            fontsize=12,
        )
        ax.text(
            0.99 - get_aspect(ax),
            0.5,
            f"{competition_2} - {season_2}",
            ha="right",
            va="center",
            color=self.text_color,
            fontsize=12,
        )
        ax.text(
            0.01 + get_aspect(ax),
            0.1,
            f"Age: {age_1}. Minutes: {minutes_1:.0f}",
            ha="left",
            va="bottom",
            color=self.text_color,
            fontsize=10,
        )
        ax.text(
            0.99 - get_aspect(ax),
            0.1,
            f"Age: {age_2}. Minutes: {minutes_2:.0f}",
            ha="right",
            va="bottom",
            color=self.text_color,
            fontsize=10,
        )

    def _plot_radar(self, ax: Axes, data: pd.DataFrame):
        params = self._get_param_names(data)
        low = [0.0] * len(params)
        high = [1.0] * len(params)

        radar = Radar(
            params,
            low,
            high,
            # whether to round any of the labels to integers instead of decimal places
            round_int=[False] * len(params),
            num_rings=4,  # the number of concentric circles (excluding center circle)
            # if the ring_width is more than the center_circle_radius then
            # the center circle radius will be wider than the width of the concentric circles
            ring_width=1,
            center_circle_radius=1,
        )
        label_radius = np.linspace(
            radar.ring_width, radar.ring_width * radar.num_rings, radar.num_rings
        )
        label_radius = radar.center_circle_radius + label_radius
        for i, label_radius in enumerate(label_radius):
            ax.text(
                0,
                label_radius,
                f"{(i+1)*25}",
                ha="center",
                va="center",
                fontsize=8,
                fontproperties=font_normal.prop,
                bbox=dict(
                    facecolor=self.facecolor,
                    edgecolor=self.circle_line_color,
                    boxstyle="round,pad=0.2",
                    lw=1,
                ),
                zorder=2,
            )

        rings_inner = radar.draw_circles(
            ax=ax, facecolor=self.facecolor, edgecolor=self.circle_line_color, zorder=1.5
        )
        radar.setup_axis(ax=ax, facecolor=self.facecolor)
        all_vertices = []
        for (_, r), color in zip(data.iterrows(), self.radar_colors):
            values = r[params].values
            _, vertices = radar.draw_radar_solid(
                values, ax=ax, kwargs=dict(alpha=0.2, color=color, lw=2, edgecolor="k", zorder=3)
            )
            all_vertices.append(vertices)

            for i, v in enumerate(vertices):
                value = r[f"{params[i]}__value"]
                ax.text(
                    v[0],
                    v[1],
                    value,
                    va="center",
                    ha="center",
                    size=8,
                    color=color,
                    bbox=dict(
                        facecolor=self.facecolor,
                        edgecolor=color,
                        boxstyle="round,pad=0.2",
                    ),
                    rotation=radar.rotation_degrees[i],
                    zorder=20,
                )
        param_labels = radar.draw_param_labels(
            ax=ax, color="#000000", fontsize=8, fontproperties=font_normal.prop
        )

        if self.center_logo_url:
            try:
                img = Image.open(urlopen(self.center_logo_url))
                ax_insert = ax.inset_axes((0.44, 0.44, 0.12, 0.12), zorder=20)
                ax_insert.axis("off")

                ax_insert.imshow(
                    img,
                )
            except Exception as exc:
                print(exc)
                pass

    def _plot_endnotes(self, ax: Axes):

        ax.text(
            1.0,
            1,
            self.watermark,
            ha="right",
            va="top",
            fontproperties=font_italic.prop,
            color=self.textcolor,
            fontsize=8,
        )
        ax.text(
            0.0,
            1,
            "European Competition stats included where applicable",
            ha="left",
            va="top",
            fontproperties=font_italic.prop,
            color=self.textcolor,
            fontsize=8,
        )

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = self._setup_figure()
        self._plot_radar(axes["radar"], data)
        self._plot_header(axes["title"], data)
        self._plot_endnotes(axes["endnote"])
        return fig, axes
