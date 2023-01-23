"""
Dashboards that create a scatter plot
where every dot represents a player

"""

from dataclasses import dataclass
from typing import Dict, Tuple, Sequence, Optional
import pandas as pd
import numpy as np
from matplotlib.axes import Axes
from matplotlib.cm import get_cmap
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from adjustText import adjust_text

from footballdashboards.dashboard.dashboard import Dashboard
from footballdashboards.helpers.fonts import font_normal, font_italic
from footballdashboards._types._dashboard_fields import (
    FigSizeField,
    FontSizeField,
    DashboardField,
    ColorField,
    DictField,
    FloatListField,
    ColorMapField,
)
from footballdashboards._types._data_accessor import _DataAccessor
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards.dashboard._data_mixins import SeasonLeagueMixin
from footballdashboards._defaults._league_colour_maps import MENS_EUROPEAN_DOMESTIC_LEAGUES
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.elements.headers import simple_title_subtitle_header
from footballdashboards.helpers.formatters import player_name_first_initial_surname_formatter


@dataclass
class ScatterTexts:
    """
    Defines the texts for a scatter dashboard
    """

    title: str
    subtitle: str = ""
    explanatory_text: str = ""


class ScatterDashboard(SeasonLeagueMixin, Dashboard):
    """
    Base class for scatter dashboards
    """

    DEFAULT_FIGSIZE = (14, 15.4)
    TITLE_SIZE = 24
    SUBTITLE_SIZE = 18
    COLOR_MARKING_THRESHOLD = 0.4
    NAME_ANNOTATION_THRESHOLD = 0.2
    TOP_BOUNDARY_MULT = 1.1
    BOTTOM_BOUNDARY_MULT = 1.1
    LEFT_BOUNDARY_MULT = 1.1
    RIGHT_BOUNDARY_MULT = 1.1
    GRID_COLOR = "silver"
    MEAN_LINE_COLOR = "ivory"
    INNER_DATA_COLOR = "silver"
    ARROW_COLOR = "darkslategray"

    figsize = FigSizeField(
        description="Figsize in centimeters, must be tuple (x, y)", default=DEFAULT_FIGSIZE
    )
    title_font_size = FontSizeField(description="Title font size in pts", default=TITLE_SIZE)
    subtitle_font_size = FontSizeField(
        description="Subtitle font size in pts", default=SUBTITLE_SIZE
    )
    color_marking_threshold = DashboardField(
        description="Percent of points that will be marked with league colour",
        default=COLOR_MARKING_THRESHOLD,
    )
    name_annotation_threshold = DashboardField(
        description="Percent of points that will be annotated with player names",
        default=NAME_ANNOTATION_THRESHOLD,
    )
    top_boundary_multiplier = DashboardField(
        description="Multiplier for the top boundary of the plot, it will be extended by to "
        "(highest_value-mean)*multiplier+mean",
        default=TOP_BOUNDARY_MULT,
    )
    bottom_boundary_multiplier = DashboardField(
        description="Multiplier for the bottom boundary of the plot, it will be extended by to "
        "mean-(mean-lowest_value)*multiplier",
        default=BOTTOM_BOUNDARY_MULT,
    )
    left_boundary_multiplier = DashboardField(
        description="Multiplier for the left boundary of the plot, it will be extended by to "
        "(lowest_value-mean)*multiplier+mean",
        default=LEFT_BOUNDARY_MULT,
    )
    right_boundary_multiplier = DashboardField(
        description="Multiplier for the right boundary of the plot, it will be extended by to "
        "mean-(mean-highest_value)*multiplier",
        default=RIGHT_BOUNDARY_MULT,
    )
    grid_color = ColorField(description="Color of the grid lines", default=GRID_COLOR)
    inner_data_color = ColorField(
        description="Color of the inner data points", default=INNER_DATA_COLOR
    )
    annotation_arrow_color = ColorField(
        description="Color of the annotation arrows", default=ARROW_COLOR
    )
    TITLE_KEY = "title"
    SCATTER_KEY = "scatter"
    ENDNOTE_KEY = "endnote"

    LEAGUE_COLUMN = "League"
    PLAYER_COLUMN = "Player"

    def __init__(
        self,
        data_accessor: _DataAccessor,
        x_column: str,
        y_column: str,
        texts: ScatterTexts,
        league_color_map: Optional[Dict[str, Tuple[str, str]]] = None,
    ):  # pylint: disable=too-many-arguments
        super().__init__(data_accessor)

        self.x_column = x_column
        self.y_column = y_column
        self.texts = texts
        self.league_color_map = league_color_map or MENS_EUROPEAN_DOMESTIC_LEAGUES

    @property
    def datasource_name(self) -> str:
        return ScatterDashboard.__name__

    def _required_data_columns(self) -> Dict[str, str]:
        return {
            self.PLAYER_COLUMN: "Player name",
            self.LEAGUE_COLUMN: "League name",
            self.x_column: self.x_column,
            self.y_column: self.y_column,
        }

    def _init_fig(self) -> PlotReturnType:
        fig = plt.figure(figsize=self.figsize)
        fig.set_facecolor(self.facecolor)
        axes = {
            k: v
            for k, v in zip(
                [self.TITLE_KEY, self.SCATTER_KEY, self.ENDNOTE_KEY],
                fig.subplots(nrows=3, height_ratios=[0.05, 0.9, 0.05]),
            )
        }
        for axis in axes.values():
            axis.set_facecolor(self.facecolor)
        for ax_idx in [self.TITLE_KEY, self.ENDNOTE_KEY]:
            axes[ax_idx].axis("off")
            axes[ax_idx].set_xlim(0, 1)
            axes[ax_idx].set_ylim(0, 1)
        return fig, axes

    def _setup_data(self, data: pd.DataFrame) -> pd.DataFrame:
        model1 = IsolationForest(contamination=self.color_marking_threshold, random_state=0)
        model2 = IsolationForest(contamination=self.name_annotation_threshold, random_state=0)

        data["inner_ring"] = model1.fit_predict(data[[self.x_column, self.y_column]])
        data["annotate"] = model2.fit_predict(data[[self.x_column, self.y_column]])
        return data

    def _setup_scatter_axes(self, axis: Axes, data: pd.DataFrame):
        max_y = (
            data[self.y_column].max() - data[self.y_column].mean()
        ) * self.top_boundary_multiplier + data[self.y_column].mean()
        min_y = (
            data[self.y_column].mean()
            - (data[self.y_column].mean() - data[self.y_column].min())
            * self.bottom_boundary_multiplier
        )
        max_x = (
            data[self.x_column].max() - data[self.x_column].mean()
        ) * self.right_boundary_multiplier + data[self.x_column].mean()
        min_x = (
            data[self.x_column].mean()
            - (data[self.x_column].mean() - data[self.x_column].min())
            * self.left_boundary_multiplier
        )
        axis.set_ylim(min_y, max_y)
        axis.set_xlim(min_x, max_x)
        axis.grid(color=self.grid_color, linestyle="--", linewidth=0.5, alpha=0.5)
        axis.set_xlabel(self.x_column, fontproperties=font_normal.prop, size=16)
        axis.set_ylabel(self.y_column, fontproperties=font_normal.prop, size=16)
        for label in axis.get_xticklabels():
            label.set_fontproperties(font_normal.prop)

        for label in axis.get_yticklabels():
            label.set_fontproperties(font_normal.prop)

    def _draw_title(self, axis: Axes):
        simple_title_subtitle_header(
            axis,
            self.texts.title,
            self.texts.subtitle,
            title_kwargs={"size": self.title_font_size},
            subtitle_kwargs={"size": self.subtitle_font_size},
        )

    def _draw_league_legend(self, axis: Axes, competitions: Sequence[str]):
        competitions = sorted(competitions)
        n_comps = len(competitions)
        for i, league in enumerate(competitions):
            border, colour = self.league_color_map[league]
            x_value = 0.01 + i * 1.0 / n_comps
            axis.scatter([x_value], [0.5], c=colour, edgecolor=border, s=100)
            inset_ax = axis.inset_axes([x_value + 0.02, 0, get_aspect(axis), 1])
            inset_ax.axis("off")
            inset_ax.imshow(self.badge_service.league_badge(league))

    def _scatter_inner_points(self, axis: Axes, data: pd.DataFrame):
        inner_df = data.loc[data["inner_ring"] == 1]
        axis.scatter(
            inner_df[self.x_column],
            inner_df[self.y_column],
            c=self.inner_data_color,
            alpha=0.5,
            zorder=2,
        )

    def _scatter_league_marked_points(self, axis: Axes, data: pd.DataFrame):
        leagues = data[self.LEAGUE_COLUMN].unique()
        outer_df = data.loc[data["inner_ring"] == -1]
        for league in leagues:
            border, color = self.league_color_map[league]
            df_ = outer_df.loc[outer_df[self.LEAGUE_COLUMN] == league]
            axis.scatter(
                df_[self.x_column], df_[self.y_column], c=color, edgecolor=border, s=100, zorder=3
            )

    def _annotate_points_on_scatter(self, axis: Axes, data: pd.DataFrame) -> list:
        annotate_df = data.loc[data["annotate"] == -1].copy()
        annotate_df["name"] = annotate_df[self.PLAYER_COLUMN].apply(
            player_name_first_initial_surname_formatter
        )

        texts = []
        props = dict(boxstyle="round", facecolor=self.facecolor, alpha=1)
        for _, row in annotate_df.iterrows():
            texts.append(
                axis.text(
                    row[self.x_column],
                    row[self.y_column],
                    row["name"],
                    size=11,
                    fontproperties=font_normal.prop,
                    bbox=props,
                    zorder=4,
                )
            )

        return texts

    def _adjust_text_positions(self, axis: Axes, texts: list):
        adjust_text(
            texts,
            ax=axis,
            only_move={"text": "xy"},
            force_points=(8, 8),
            force_objects=(8, 8),
            arrowprops=dict(arrowstyle="->", color=self.annotation_arrow_color, lw=1),
            zorder=7,
        )

    def _plot_scatter(self, axis: Axes, data: pd.DataFrame):
        self._scatter_inner_points(axis, data)
        self._scatter_league_marked_points(axis, data)
        annotations = self._annotate_points_on_scatter(axis, data)
        self._adjust_text_positions(axis, annotations)

    def _write_endnote_annotation(self, axis: Axes):
        if self.texts.explanatory_text:
            axis.text(
                0.01,
                1.1,
                self.texts.explanatory_text,
                size=10,
                ha="left",
                va="bottom",
                fontproperties=font_italic.prop,
            )

    def _write_watermark(self, axis: Axes):
        if self.watermark:
            axis.text(
                0.99,
                0.5,
                self.watermark,
                size=10,
                va="center",
                ha="center",
                fontproperties=font_normal.prop,
            )

    def _plot_endnote(self, axis: Axes, data: pd.DataFrame):
        competitions = data[self.LEAGUE_COLUMN].unique()
        self._draw_league_legend(axis, competitions)
        self._write_endnote_annotation(axis)
        self._write_watermark(axis)

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = self._init_fig()

        data = self._setup_data(data)
        self._draw_title(axes[self.TITLE_KEY])
        self._setup_scatter_axes(axes[self.SCATTER_KEY], data)
        self._plot_endnote(axes[self.ENDNOTE_KEY], data)
        self._plot_scatter(axes[self.SCATTER_KEY], data)
        return fig, axes


class ScatterWithQuadrantsDashboard(ScatterDashboard):
    """A dashboard that plots a scatter plot with
    four quadrants separated by the mean of the x and y columns.
    Each quadrant can be coloured differently and labelled. with an independent annotation.

    If the quadrant annotations overlap label text, you can experiment with the
    `right_boundary_multiplier`, `left_boundary_multiplier`, `top_boundary_multiplier` and
    `bottom_boundary_multiplier` parameters to adjust the boundaries of the quadrants.
    """

    MEAN_LINE_COLOR = "ivory"
    TOP_RIGHT_QUADRANT_COLOR = "green"
    TOP_LEFT_QUADRANT_COLOR = "yellow"
    BOTTOM_RIGHT_QUADRANT_COLOR = "yellow"
    BOTTOM_LEFT_QUADRANT_COLOR = "red"

    QUADRANT_ANNOTATION_LOCATIONS = {
        "topright": {"x": 0.99, "y": 0.99, "va": "top", "ha": "right"},
        "topleft": {"x": 0.01, "y": 0.99, "va": "top", "ha": "left"},
        "bottomright": {"x": 0.99, "y": 0.01, "va": "bottom", "ha": "right"},
        "bottomleft": {"x": 0.01, "y": 0.01, "va": "bottom", "ha": "left"},
    }

    mean_line_color = ColorField(
        description="Color of the line separating the quadrants", default=MEAN_LINE_COLOR
    )
    top_right_quadrant_color = ColorField(
        description="Color of the top right quadrant", default=TOP_RIGHT_QUADRANT_COLOR
    )
    top_left_quadrant_color = ColorField(
        description="Color of the top left quadrant", default=TOP_LEFT_QUADRANT_COLOR
    )
    bottom_right_quadrant_color = ColorField(
        description="Color of the bottom right quadrant", default=BOTTOM_RIGHT_QUADRANT_COLOR
    )
    bottom_left_quadrant_color = ColorField(
        description="Color of the bottom left quadrant", default=BOTTOM_LEFT_QUADRANT_COLOR
    )
    quadrant_texts = DictField(
        description="Texts to be displayed in the quadrants",
        acceptable_keys=["topright", "topleft", "bottomright", "bottomleft"],
    )

    def _draw_quadrants(self, axis: Axes, data: pd.DataFrame):
        mean_x = data[self.x_column].mean()
        mean_y = data[self.y_column].mean()
        min_x, max_x = axis.get_xlim()
        min_y, max_y = axis.get_ylim()

        axis.axvline(
            [mean_x],
            ymin=0,
            ymax=1,
            linestyle="--",
            lw=1,
            color=self.mean_line_color,
            zorder=1,
        )
        axis.axhline(
            [mean_y],
            xmin=0,
            xmax=1,
            linestyle="--",
            lw=1,
            color=self.mean_line_color,
            zorder=1,
        )
        axis.fill(
            [min_x, min_x, mean_x, mean_x],
            [mean_y, max_y, max_y, mean_y],
            color=self.top_left_quadrant_color,
            alpha=0.1,
            zorder=0.9,
        )
        axis.fill(
            [min_x, min_x, mean_x, mean_x],
            [mean_y, min_y, min_y, mean_y],
            color=self.bottom_left_quadrant_color,
            alpha=0.1,
            zorder=0.9,
        )
        axis.fill(
            [max_x, max_x, mean_x, mean_x],
            [mean_y, min_y, min_y, mean_y],
            color=self.bottom_right_quadrant_color,
            alpha=0.1,
            zorder=0.9,
        )
        axis.fill(
            [max_x, max_x, mean_x, mean_x],
            [mean_y, max_y, max_y, mean_y],
            color=self.top_right_quadrant_color,
            alpha=0.1,
            zorder=0.9,
        )

    def _annotate_quadrants(self, axis: Axes):
        props = dict(boxstyle="round", facecolor=self.facecolor, alpha=1)
        for location, annotation in self.quadrant_texts.items():
            placement = self.QUADRANT_ANNOTATION_LOCATIONS[location]
            axis.text(
                s=annotation,
                transform=axis.transAxes,
                bbox=props,
                fontproperties=font_normal.prop,
                size=12,
                **placement,
                zorder=6
            )

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = super()._plot_data(data)
        self._draw_quadrants(axes[self.SCATTER_KEY], data)
        self._annotate_quadrants(axes[self.SCATTER_KEY])
        return fig, axes


class ScatterWithRegressionDashboard(ScatterDashboard):
    """A dashboard that plots a scatter plot with a regression line
    and a colorfan indicating distance from regression line
    """

    REGRESSION_LINE_COLOR = "black"
    FAN_COLORMAP = "RdYlGn"
    REGRESSION_ANNOTATION_LOCATIONS = {
        "topleft": {"x": 0.01, "y": 0.99, "va": "top", "ha": "left"},
        "bottomright": {"x": 0.99, "y": 0.01, "va": "bottom", "ha": "right"},
    }

    regression_line_color = ColorField(
        description="Color of the regression line", default=REGRESSION_LINE_COLOR
    )
    regression_fan_multipliers = FloatListField(
        description="Multipliers for the regression slope line which"
        " are used to separate into different color sections",
        default=[1.6, 1.3, 1.0, 1 / 1.3, 1 / 1.6],
    )
    regression_fan_colormap = ColorMapField(
        description="Matplotlib colormap name for the regression fan", default=FAN_COLORMAP
    )
    regression_annotation_texts = DictField(
        description="Texts to be displayed in the regression fan,"
        " one for the best triangle and one for the worst",
        acceptable_keys=["topleft", "bottomright"],
    )

    def _draw_regression_and_fan(self, axis: Axes, data: pd.DataFrame):
        cmap = get_cmap(self.regression_fan_colormap)
        poly_params = np.polyfit(data[self.x_column], data[self.y_column], 1)
        x_values = [axis.get_xlim()[0], axis.get_xlim()[1]]
        reg_line = np.poly1d(poly_params)
        mults = sorted(self.regression_fan_multipliers)
        axis.plot(x_values, reg_line(x_values), color=self.regression_line_color, zorder=1, lw=2)
        for i, coef in enumerate(mults):
            poly = np.poly1d([poly_params[0] * coef, poly_params[1]])
            if i == 0:
                axis.fill_between(
                    x_values,
                    poly(x_values),
                    np.ones(len(x_values)) * axis.get_ylim()[0],
                    color=cmap(0.0),
                    alpha=0.1,
                    zorder=0.9,
                )

            else:
                p_prev = np.poly1d([poly_params[0] * mults[i - 1], poly_params[1]])
                axis.fill_between(
                    x_values,
                    poly(x_values),
                    p_prev(x_values),
                    color=cmap(i / (len(mults) + 1)),
                    alpha=0.1,
                    zorder=0.9,
                )

        axis.fill_between(
            x_values,
            poly(x_values),
            np.ones(len(x_values)) * axis.get_ylim()[1],
            color=cmap(1.0),
            alpha=0.1,
            zorder=0.9,
        )

    def _annotate_regression(self, axis: Axes):
        props = dict(boxstyle="round", facecolor=self.facecolor, alpha=1)
        for loc, annotation in self.regression_annotation_texts.items():
            placement = self.REGRESSION_ANNOTATION_LOCATIONS[loc]
            axis.text(
                s=annotation,
                transform=axis.transAxes,
                bbox=props,
                fontproperties=font_normal.prop,
                size=12,
                **placement,
                zorder=6
            )

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = super()._plot_data(data)
        self._draw_regression_and_fan(axes[self.SCATTER_KEY], data)
        self._annotate_regression(axes[self.SCATTER_KEY])
        return fig, axes
