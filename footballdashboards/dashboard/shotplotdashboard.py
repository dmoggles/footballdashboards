from typing import Dict
import pandas as pd
from matplotlib.axes import Axes
from mplsoccer.pitch import VerticalPitch
from footballdashboards.dashboard.dashboard import Dashboard
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards._types._dashboard_fields import ColorField, DashboardField
from footballdashboards.helpers.mplsoccer_helpers import make_grid
from footballdashboards.dashboard._data_mixins import PlayerSeasonsLeaguesMixin


class ShotPlotDashboard(PlayerSeasonsLeaguesMixin, Dashboard):
    PITCH_COLOR = "#000011"
    PITCH_LINE_COLOR = "ivory"
    FIG_HEIGHT = 10
    GOAL_COLOR_MARKER = "blue"
    SHOT_COLOR_MARKER = "grey"
    BIG_CHANCE_EDGE_COLOR = "red"
    MIN_SHOT_SIZE = 30
    MAX_SHOT_SIZE = 600
    pitch_color = ColorField(description="Pitch background colour", default=PITCH_COLOR)
    line_color = ColorField(description="Pitch line colour", default=PITCH_LINE_COLOR)
    goal_marker_color = ColorField(description="Goal marker colour", default=GOAL_COLOR_MARKER)
    shot_marker_color = ColorField(description="Shot marker colour", default=SHOT_COLOR_MARKER)
    fig_height = DashboardField(description="Figure height", default=FIG_HEIGHT)
    big_chance_edge_color = ColorField(
        description="Big chance edge colour", default=BIG_CHANCE_EDGE_COLOR
    )
    min_shot_size = DashboardField(description="Minimum shot size", default=MIN_SHOT_SIZE)
    max_shot_size = DashboardField(description="Maximum shot size", default=MAX_SHOT_SIZE)
    TITLE_IDX = "title"
    ENDNOTE_IDX = "endnote"
    PITCH_IDX = "pitch"

    @property
    def datasource_name(self) -> str:
        return ShotPlotDashboard.__name__

    def _required_data_columns(self) -> Dict[str, str]:
        return {
            "player": "Player name",
            "season": "Season",
            "league": "League",
            "x": "X coordinate of the shot, 0 is the left goal line, 100 is the right goal line",
            "y": "Y coordinate of the shot",
            "result": "Result of the shot",
            "assisting_player": "Player that assisted the shot",
            "xg": "Expected goals for the shot",
            "big_chance": "Whether the shot was a big chance",
        }

    def _setup_pitch(self) -> VerticalPitch:
        pitch = VerticalPitch(
            pitch_type="opta", half=True, pitch_color=self.pitch_color, line_color=self.line_color
        )
        return pitch

    def _setup_figure(self, pitch: VerticalPitch) -> PlotReturnType:
        fig, axes = make_grid(
            pitch,
            self.fig_height,
            endnote_height=0.05,
            title_height=0.05,
            title_space=0,
            endnote_space=0,
        )
        for ax_idx in [self.TITLE_IDX, self.ENDNOTE_IDX]:
            axes[ax_idx].axis("off")
            axes[ax_idx].set_facecolor(self.facecolor)

        return fig, axes

    def _plot_shots(self, pitch: VerticalPitch, axis: Axes, data: pd.DataFrame):

        goals_big_change = data[(data["result"] == 1) & (data["big_chance"] == 1)]
        goals_not_big_change = data[(data["result"] == 1) & (data["big_chance"] == 0)]
        shots_big_change = data[(data["result"] == 0) & (data["big_chance"] == 1)]
        shots_not_big_change = data[(data["result"] == 0) & (data["big_chance"] == 0)]
        pitch.scatter(
            goals_big_change["x"],
            goals_big_change["y"],
            c=self.goal_marker_color,
            s=(self.max_shot_size - self.min_shot_size) * goals_big_change["xg"]
            + self.min_shot_size,
            edgecolors=self.big_chance_edge_color,
            ax=axis,
            alpha=0.8,
            zorder=3,
            lw=2,
        )
        pitch.scatter(
            goals_not_big_change["x"],
            goals_not_big_change["y"],
            c=self.goal_marker_color,
            s=(self.max_shot_size - self.min_shot_size) * goals_not_big_change["xg"]
            + self.min_shot_size,
            ax=axis,
            alpha=0.8,
            zorder=3,
        )
        pitch.scatter(
            shots_big_change["x"],
            shots_big_change["y"],
            c=self.shot_marker_color,
            s=(self.max_shot_size - self.min_shot_size) * shots_big_change["xg"]
            + self.min_shot_size,
            edgecolors=self.big_chance_edge_color,
            ax=axis,
            alpha=0.5,
            zorder=2,
            lw=2,
        )
        pitch.scatter(
            shots_not_big_change["x"],
            shots_not_big_change["y"],
            c=self.shot_marker_color,
            s=(self.max_shot_size - self.min_shot_size) * shots_not_big_change["xg"]
            + self.min_shot_size,
            ax=axis,
            alpha=0.5,
            zorder=2,
        )

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        pitch = self._setup_pitch()
        fig, axes = self._setup_figure(pitch)
        self._plot_shots(pitch, axes[self.PITCH_IDX], data)
        return fig, axes
