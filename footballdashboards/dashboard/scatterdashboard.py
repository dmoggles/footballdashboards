from typing import Dict, Tuple
import numpy as np
from pandas import DataFrame
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards.dashboard.dashboard import Dashboard
from footballdashboards._types._dashboard_fields import FigSizeField, ColorMapField, ColorField
from footballdashboards.helpers.mclachbot_helpers import get_ball_logo2
from footballdashboards.helpers.matplotlib import get_aspect
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.axes import Axes
import cmasher as cmr
from adjustText import adjust_text
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy.interpolate import interp1d
from footballdashboards.helpers.fonts import (
    font_normal,
    font_bold,
    font_italic,
    font_varsity,
    font_berpatroli,
    font_europa,
    font_royal_crescent,
)
from footballdashboards.helpers.formatters import smartest_name_formatter_yet
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import json

from matplotlib.colors import ListedColormap
from matplotlib.cm import register_cmap

ListedColormap(
    [
        "#377eb8",
        "#ff7f00",
        "#4daf4a",
        "#f781bf",
        "#a65628",
        "#984ea3",
        "#999999",
        "#e41a1c",
        "#dede00",
    ],
    "cb_friendly",
)
register_cmap(
    "cb_friendly",
    cmap=ListedColormap(
        [
            "#377eb8",
            "#ff7f00",
            "#4daf4a",
            "#f781bf",
            "#a65628",
            "#984ea3",
            "#999999",
            "#e41a1c",
            "#dede00",
        ]
    ),
)


class ScatterDashboard(Dashboard):
    figsize = FigSizeField("figsize", default=(10, 10))
    title = ""
    color_map = ColorMapField("color_map", default="viridis")
    categorical_color_map = ColorMapField("categorical_color_map", default="Dark2")
    default_color = ColorField("default_color", default="blue")
    min_size = 10
    max_size = 100
    default_size = 50
    means = False
    std_devs = False

    def _required_data_columns(self) -> Dict[str, str]:
        return {}

    @property
    def datasource_name(self) -> str:
        return "ScatterDataSource"

    def _draw_line(self, ax: Axes):
        color = "black"
        ax.plot([0.0, 1.0], [0.0, 0.0], lw=7, color=color, zorder=10)

    def _setup_figure(self, data: pd.DataFrame) -> Tuple[Figure, Dict[str, Axes]]:
        if "size_axis" in data.columns or (
            "color_axis" in data.columns and data["color_axis"].dtype == "O"
        ):
            mosaic_layout = [["header"], ["scatter"], ["footer"]]
            height_ratios = [0.075, 0.85, 0.075]
        else:
            mosaic_layout = [["header"], ["scatter"]]
            height_ratios = [0.075, 0.925]
        fig = Figure(
            figsize=self.figsize,
            tight_layout=True,
            constrained_layout=True,
            facecolor=self.facecolor,
        )

        axes = fig.subplot_mosaic(
            mosaic_layout,
            gridspec_kw={
                "height_ratios": height_ratios,
            },
        )
        for ax in axes.values():
            if ax != axes["scatter"]:
                ax.axis("off")
            if ax == axes["scatter"]:
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["bottom"].set_visible(False)
                ax.spines["left"].set_visible(False)

        return fig, axes

    def _league_str(self, league_list):
        league_str = ""
        if (
            set(["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"])
            - set(league_list)
            == set()
        ):
            league_str = "Top 5 Leagues"
            league_list = list(
                set(league_list)
                - set(["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"])
            )
        if len(league_list) == 0:
            return league_str
        if len(league_list) > 3:
            if league_str:
                league_str += ", "
            league_str += ", ".join(league_list[:3]) + " and " + str(len(league_list) - 3) + " more"
        else:
            if league_str:
                league_str += ", "
            league_str += ", ".join(league_list)
        # replace the last comma with an and
        league_str = league_str.rsplit(", ", 1)
        if len(league_str) > 1:
            league_str = " and ".join(league_str)
        else:
            league_str = league_str[0]
        return league_str

    def _draw_title(self, data: DataFrame, ax: Axes):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        filters = json.loads(data["filter_data"].iloc[0])
        minutes = filters["minutes_filter"]
        position_filter = filters["position_filter"]
        if position_filter:
            position_str = ", ".join([f"{p}s" for p in position_filter])
            # replace the last comma with an and
            position_str = position_str.rsplit(", ", 1)
            if len(position_str) > 1:
                position_str = " and ".join(position_str)
            else:
                position_str = position_str[0]

        else:
            position_str = "All Positions"
        if minutes > 0:
            position_str += f" with >{minutes:.0f}'"

        if self.title:
            title_text = self.title
        else:
            x_axis_name = self._format_label(data["x_axis_name"].iloc[0])
            y_axis_name = self._format_label(data["y_axis_name"].iloc[0])
            title_text = f"{x_axis_name} vs {y_axis_name}"
        ax.text(
            0.0, 0.95, title_text, fontsize=20, ha="left", va="top", fontproperties=font_europa.prop
        )
        leagues_str = self._league_str(data["comp"].unique())
        second_line_str = leagues_str
        second_line_str += " | "
        second_line_str += f"Season {data['season'].iloc[0]}"
        second_line_str += " | "
        second_line_str += position_str
        ax.text(
            0.0,
            0.5,
            second_line_str,
            fontsize=12,
            ha="left",
            va="top",
            fontproperties=font_normal.prop,
        )
        self._draw_line(ax)

    def _size(self, data: DataFrame) -> DataFrame:
        if "size_axis" in data.columns:
            scaler = MinMaxScaler(feature_range=(self.min_size, self.max_size))
            return scaler.fit_transform(data[["size_axis"]])
        else:
            return np.full(data.shape[0], self.default_size)

    def _format_label(self, label: str) -> str:
        return label

    def _colors(self, data: DataFrame) -> str:
        if "color_axis" in data.columns:
            if data["color_axis"].dtype == "O":  # categorical
                colormap_name = self.categorical_color_map
                cmap = cmr.get_sub_cmap(colormap_name, 0, 1)
                return cmap(data["color_axis"].astype("category").cat.codes)
            else:
                scaler = MinMaxScaler()
                colormap_name = self.color_map
                cmap = cmr.get_sub_cmap(colormap_name, 0, 1)
                return cmap(scaler.fit_transform(data[["color_axis"]]))
        else:
            return self.default_color

    def _draw_colorbar(self, fig: Figure, ax: Axes, scatter, color_axis_name, color_axis):
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.50)
        cbar = fig.colorbar(scatter, cax=cax, orientation="vertical", aspect=100)
        cbar.set_label(color_axis_name)
        cbar.set_ticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        min = color_axis.min()
        max = color_axis.max()
        cbar.set_ticklabels(
            [
                f"{min:.2f}",
                f"{min + (max-min)*0.2:.2f}",
                f"{min + (max-min)*.4:.2f}",
                f"{min + (max-min)*.6:.2f}",
                f"{min + (max-min)*.8:.2f}",
                f"{max:.2f}",
            ],
            fontproperties=font_normal.prop,
        )
        # cbar.ax.yaxis.set_label_position('bottom')
        cbar.ax.yaxis.set_ticks_position("left")

    def _annotate(self, data: DataFrame, ax: Axes, scatter):
        annotated = data[data["annotate"]].copy()
        if "player" in annotated.columns:
            annotated_column = "player"
            annotated[annotated_column] = annotated[annotated_column].apply(
                smartest_name_formatter_yet
            )
        else:
            annotated_column = "squad"
        texts = []
        props = dict(boxstyle="round", facecolor=self.facecolor, alpha=1)
        for _, row in annotated.iterrows():
            texts.append(
                ax.text(
                    row["x_axis"],
                    row["y_axis"],
                    row[annotated_column],
                    ha="left",
                    va="bottom",
                    size=11,
                    fontproperties=font_normal.prop,
                    # bbox=props,
                    zorder=30,
                )
            )
        adjust_text(
            texts,
            ax=ax,
            objects=scatter,
            only_move={"text": "xy"},
            # force_text=(5,5),
            # force_static=(5,5),
            # force_explode=(0.2,1),
            ensure_inside_axes=True,
            avoid_self=True,
            arrowprops=dict(arrowstyle="simple", color="black", lw=1),
            zorder=30,
        )

    def _draw_scatter(self, data: DataFrame, ax: Axes, fig: Figure, footer_ax: Axes):
        ax.set_facecolor(self.facecolor)
        x_axis_name = data["x_axis_name"].iloc[0]
        y_axis_name = data["y_axis_name"].iloc[0]
        if "size_axis_name" in data.columns:
            size_axis_name = data["size_axis_name"].iloc[0]
        else:
            size_axis_name = None
        if "color_axis_name" in data.columns:
            color_axis_name = data["color_axis_name"].iloc[0]
        else:
            color_axis_name = None

        size = self._size(data)
        colors = self._colors(data)
        scatter = ax.scatter(data["x_axis"], data["y_axis"], s=size, c=colors, alpha=0.8, zorder=20)
        if self.means:
            ax.axvline(
                data["x_axis"].mean(), color="darkgreen", linestyle="dashed", linewidth=1, zorder=2
            )
            ax.axhline(
                data["y_axis"].mean(), color="darkgreen", linestyle="dashed", linewidth=1, zorder=2
            )

        if self.std_devs:
            # draw std devs as a filled square area
            x_mean = data["x_axis"].mean()
            y_mean = data["y_axis"].mean()
            x_std = data["x_axis"].std()
            y_std = data["y_axis"].std()
            ax.add_patch(
                Rectangle(
                    (x_mean - x_std, y_mean - y_std),
                    2 * x_std,
                    2 * y_std,
                    fill=True,
                    color="green",
                    alpha=0.1,
                    zorder=3,
                )
            )
        ax.grid(True, alpha=0.4, zorder=1, linestyle="dotted")
        ax.set_xlabel(self._format_label(x_axis_name))
        ax.set_ylabel(self._format_label(y_axis_name))
        plotted_color_legend = False

        legend_kwargs = dict(
            title_fontsize=8,
            fontsize=8,
            frameon=False,
            bbox_to_anchor=(0, 0, 1, 1),
            prop=font_normal.prop,
            columnspacing=0.5,
        )

        if "color_axis" in data.columns:
            if data["color_axis"].dtype == "O":  # categorical
                # draw legend in the footer
                # footer_ax.axis('off')
                plotted_color_legend = True
                legend_elements = [
                    Rectangle(
                        (0, 0),
                        1,
                        1,
                        color=cmr.get_sub_cmap(self.categorical_color_map, 0, 1)(i),
                        label=cat,
                    )
                    for i, cat in enumerate(data["color_axis"].astype("category").cat.categories)
                ]
                legend = footer_ax.legend(
                    handles=legend_elements,
                    title=self._format_label(color_axis_name),
                    loc="upper left",
                    ncols=int(np.ceil(len(legend_elements) / 2)),
                    **legend_kwargs,
                )
                if "size_axis" in data.columns:
                    footer_ax.add_artist(legend)

            else:
                self._draw_colorbar(
                    fig, ax, scatter, self._format_label(color_axis_name), data["color_axis"]
                )
        if "size_axis" in data.columns:
            # draw legend in the footer
            # footer_ax.axis('off')
            # sizes = [self.min_size, (self.min_size + self.max_size) / 2, self.max_size]
            min_value = data["size_axis"].min()
            max_value = data["size_axis"].max()
            location = "upper left" if not plotted_color_legend else "upper right"
            interp = interp1d(
                [self.min_size, self.max_size], [min_value, max_value], fill_value="extrapolate"
            )
            handles, labels = scatter.legend_elements("sizes", num=5, func=lambda x: interp(x))
            # map sizes to values

            # sizes = interp(labels)
            legend = footer_ax.legend(
                handles,
                labels,
                title=self._format_label(size_axis_name),
                ncols=int(np.ceil(len(handles) / 2)),
                loc=location,
                **legend_kwargs,
            )

        self._annotate(data, ax, scatter)
        left_bottom, right_top = ax.get_position() * ax.figure.get_size_inches()
        width, height = right_top - left_bottom
        aspect = height / width

        logo_size = 0.2
        logo_inset_ax = ax.inset_axes(
            [1 - logo_size * aspect, 0.0, aspect * logo_size, logo_size], alpha=0.3, zorder=0.1
        )
        logo_inset_ax.imshow(get_ball_logo2(), alpha=0.5)
        logo_inset_ax.axis("off")
        ax.text(
            0.01,
            0.0,
            "Data by: www.fbref.com",
            fontsize=8,
            ha="left",
            va="bottom",
            transform=ax.transAxes,
            zorder=100,
            alpha=0.5,
            fontproperties=font_normal.prop,
        )

    def _plot_data(self, data: DataFrame) -> Tuple[Figure, Dict[str, Axes]]:
        fig, axes = self._setup_figure(data)
        self._draw_title(data, axes["header"])
        self._draw_scatter(data, axes["scatter"], fig, axes["footer"] if "footer" in axes else None)
        # self._draw_footer(data, axes['logo'])
        return fig, axes
