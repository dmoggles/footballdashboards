from typing import Dict, List

import pandas as pd
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards.dashboard.dashboard import Dashboard
from matplotlib.figure import Figure
from mplsoccer import Radar
import numpy as np
from footballdashboards.helpers.fonts import font_normal, font_europa
from footballdashboards._types._dashboard_fields import ColorField, ColorListField
from footballdashboards.helpers.mclachbot_helpers import get_ball_logo, McLachBotBadgeService
from matplotlib.colors import to_rgba
from footballdashboards.helpers.matplotlib import get_aspect
from matplotlib.patches import Rectangle


class TeamRankRadarDashboard(Dashboard):
    STRAIGHT_LINE_COLOUR_DEFAULT = "#888888"
    SLICE_COLORMAP = "coolwarm_r"

    radar_colors = ColorListField(
        description="Colors of radars drawn", default=["#3772FF", "#F038FF", "#FC7A57", "#31393C"]
    )
    circle_line_color = ColorField(
        description="circle line colour", default=STRAIGHT_LINE_COLOUR_DEFAULT
    )

    @property
    def datasource_name(self) -> str:
        return "TeamRankComparision"

    def _required_data_columns(self) -> Dict[str, str]:
        return {}

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = self._setup_figure()
        self._plot_radar(axes["radar"], data)
        self._plot_header(axes["title"], data)
        self._plot_endnote(axes["endnote"])
        return fig, axes

    def _plot_endnote(self, ax):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.text(
            0.98,
            1,
            "Analysis and Implementation:\n@mclachbot and @ChicagoDmitry\nData from www.fbref.com",
            ha="right",
            va="top",
            fontsize=8,
            color="black",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.02,
            1,
            "Performance: xPts\nAttack: open play xG/90\nDefense: open play xGA/90",
            ha="left",
            va="top",
            fontsize=7,
            color="black",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.25,
            1,
            "Duels: duels won/90\nPressing: PPDA\nSet Pieces: set piece xGD/90",
            ha="left",
            va="top",
            fontsize=7,
            color="black",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.48,
            1,
            "Box Efficiency: (GD-xGD)/90\nCounter: % shot from counterattacks\nPossession: % of time in possession",
            ha="left",
            va="top",
            fontsize=7,
            color="black",
            fontproperties=font_normal.prop,
        )

    def _plot_header(self, ax, data):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        n_teams = len(data)
        if n_teams == 2:
            mid_points = [0.25, 0.75]
        elif n_teams == 3:
            mid_points = [0.2, 0.5, 0.8]
        elif n_teams == 4:
            mid_points = [0.15, 0.375, 0.625, 0.85]

        for i, (_, r) in enumerate(data.iterrows()):
            badge_height = 0.7
            badge_width = badge_height * get_aspect(ax)
            logo_axis = ax.inset_axes(
                (mid_points[i] - badge_width / 2, (1 - badge_height) / 2, badge_width, badge_height)
            )

            logo_axis.axis("off")
            try:
                badge = McLachBotBadgeService().team_badge(r["competition"], r["team_name"])
                logo_axis.imshow(badge, zorder=1, alpha=0.8)
            except Exception as exc:
                print(exc)
                pass
            logo_axis.add_patch(
                Rectangle(
                    (0, 0),
                    1,
                    1,
                    facecolor=self.facecolor,
                    edgecolor=self.radar_colors[i],
                    lw=2,
                    zorder=2,
                )
            )
        game_texts = [f"Games: {r['games']:.0f}" for _, r in data.iterrows()]
        self._draw_line(ax, n_teams, game_texts, mid_points, 0.15, 0)
        league_shorts = {
            "EFL Championship": "Championship",
            "EFL League One": "League One",
            "Brasilian Serie A": "Brasileiro",
            "Argentine Primera": "Primera",
            "Jupiler Pro League": "JPL",
        }
        self._draw_line(
            ax,
            n_teams,
            [
                f"{s} - {l}"
                for s, l in zip(
                    data["season"].values,
                    data["decorated_league_name"].apply(lambda x: league_shorts.get(x, x)).values,
                )
            ],
            mid_points,
            0.15,
            0.85,
        )

    def _draw_line(self, ax, n_teams: int, texts: List[int], mid_points, height, bottom):
        height = height + bottom

        if n_teams == 2:
            ax.fill(
                [0.04, 0.51, 0.49, 0.04], [height, height, bottom, bottom], c=self.radar_colors[0]
            )
            ax.fill(
                [0.49, 0.96, 0.96, 0.51], [bottom, bottom, height, height], c=self.radar_colors[1]
            )

        elif n_teams == 3:
            ax.fill(
                [0.04, 0.34, 0.32, 0.04], [height, height, bottom, bottom], c=self.radar_colors[0]
            )
            ax.fill(
                [0.32, 0.65, 0.67, 0.34], [bottom, bottom, height, height], c=self.radar_colors[1]
            )
            ax.fill(
                [0.65, 0.96, 0.96, 0.67], [bottom, bottom, height, height], c=self.radar_colors[2]
            )

        elif n_teams == 4:
            ax.fill(
                [0.04, 0.26, 0.24, 0.04], [height, height, bottom, bottom], c=self.radar_colors[0]
            )
            ax.fill(
                [0.24, 0.49, 0.51, 0.26], [bottom, bottom, height, height], c=self.radar_colors[1]
            )
            ax.fill(
                [0.49, 0.74, 0.76, 0.51], [bottom, bottom, height, height], c=self.radar_colors[2]
            )
            ax.fill(
                [0.74, 0.96, 0.96, 0.76], [bottom, bottom, height, height], c=self.radar_colors[3]
            )

        for year, midpoint in zip(texts, mid_points):
            ax.text(
                midpoint,
                (height + bottom) / 2,
                year,
                ha="center",
                va="center",
                fontsize=10,
                fontproperties=font_europa.prop,
                color=self.facecolor,
            )

    def _setup_figure(self):
        fig = Figure(figsize=(6.75, 8), dpi=100, facecolor=self.facecolor)
        axes = {}
        axes["radar"] = fig.add_axes((0, 0.01, 1, 0.86), facecolor=self.facecolor, aspect="equal")
        axes["title"] = fig.add_axes((0, 0.88, 1.0, 0.13), facecolor=self.facecolor)
        axes["title"].axis("off")
        axes["endnote"] = fig.add_axes((0, 0, 1, 0.01), facecolor=self.facecolor)
        axes["endnote"].axis("off")
        return fig, axes

    def _get_param_names(self, data: pd.DataFrame) -> List[str]:
        params = [c for c in data.columns if c[0] == c[0].upper()]
        return params

    def _plot_radar(self, ax, data):
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

        radar.setup_axis(ax=ax, facecolor=self.facecolor)

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
        param_labels = radar.draw_param_labels(
            ax=ax, color="#000000", fontsize=8, fontproperties=font_normal.prop
        )
        all_vertices = []
        rings_inner = radar.draw_circles(
            ax=ax, facecolor=self.facecolor, edgecolor=self.circle_line_color, zorder=1.5
        )

        for (_, r), color in zip(data.iterrows(), self.radar_colors):
            values = r[params].values
            _, vertices = radar.draw_radar_solid(
                values, ax=ax, kwargs=dict(color=to_rgba(color, 0.2), lw=2, zorder=3, ec=color)
            )
            all_vertices.append(vertices)

            for i, v in enumerate(vertices):
                value = int(r[f"{params[i]}"] * 100)
                if i == 0:
                    bbox = dict(
                        facecolor=color,
                        edgecolor=color,
                        boxstyle="circle,pad=0.2",
                    )
                    text_color = self.facecolor
                else:
                    bbox = dict(
                        facecolor=self.facecolor,
                        edgecolor=color,
                        boxstyle="circle,pad=0.2",
                    )
                    text_color = color
                ax.text(
                    v[0],
                    v[1],
                    value,
                    va="center",
                    ha="center",
                    size=8,
                    color=text_color,
                    bbox=bbox,
                    rotation=radar.rotation_degrees[i],
                    zorder=20,
                )
        try:
            img = get_ball_logo()
            ax_insert = ax.inset_axes((0.44, 0.44, 0.12, 0.12), zorder=20)
            ax_insert.axis("off")

            ax_insert.imshow(
                img,
            )
        except Exception as exc:
            print(exc)
            pass
