from typing import Dict
import pandas as pd
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards._types._dashboard_fields import FigSizeField, ColorListField, ColorField
from footballdashboards.helpers.fonts import font_normal, font_bold, font_mono, font_italic
from footballdashboards.dashboard.dashboard import Dashboard
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Dict, Tuple
from matplotlib.lines import Line2D
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService, get_ball_logo2

from matplotlib.patches import FancyBboxPatch


class ButterflyDashboard(Dashboard):
    fig_size = FigSizeField("Figure size", (7, 10))
    underbar_color = ColorField("Underbar color", "lightblue")
    bar_colors = ColorListField("Bar colors", ["red", "blue"])
    second_textcolor = ColorField("Second text color", "grey")
    EXPLAIN_TEXT = ""
    EXPLAIN_TEXT_PLACEMENT = 0.5

    def _format_total(self, n: float):
        return f"{n:.0f}"

    def _required_data_columns(self) -> Dict[str, str]:
        return {}

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = self._setup_figure()
        self._plot_bars(data, axes["plot"])
        self._plot_endnote(axes["endnote"])
        self._plot_title(data, axes["header"], fig)
        return fig, axes

    def _setup_figure(self) -> Tuple[Figure, Dict[str, Axes]]:
        fig = Figure(figsize=self.fig_size, constrained_layout=True, dpi=100)
        fig.set_facecolor(self.facecolor)
        axes = fig.subplot_mosaic(
            [["header"], ["plot"], ["endnote"]], height_ratios=[0.1, 0.8, 0.1]
        )
        for ax in axes.values():
            ax.axis("off")

        return fig, axes

    def _plot_bars(self, data: pd.DataFrame, ax: Axes):
        data = data.copy()
        data["_total_value"] = data[self.BAR_COLUMNS].sum(axis=1)
        max_value = data["_total_value"].max()
        max_width = max_value * 2
        home_team_df = data.loc[data["is_home_team"] == 1]
        away_team_df = data.loc[data["is_home_team"] == 0]
        topx = ax.twiny()
        topx.set_axis_off()
        if self.UNDERBAR_COLUMN:
            max_value_secondary = data[self.UNDERBAR_COLUMN].max()

            max_width_secondary = max_value_secondary * 2

        for i, _df in enumerate([home_team_df, away_team_df]):
            if i == 0:
                m = -1
            else:
                m = 1
            _df = _df.sort_values("_total_value", ascending=False)
            _df = _df.loc[_df["position"].isna() == False]
            _df["idx"] = range(0, len(_df))
            _df["position"] = _df["position"].apply(lambda x: self.format_position(x))
            _df["pos_color"] = _df["position"].apply(lambda x: self.get_position_color(x))
            for i, (col, color) in enumerate(zip(self.BAR_COLUMNS, self.bar_colors)):
                if i == 0:
                    ax.barh(
                        -1 * _df["idx"],
                        m * _df[col],
                        left=m * 0.02 * max_width,
                        color=color,
                        height=0.7,
                        linewidth=0,
                    )
                else:
                    ax.barh(
                        -1 * _df["idx"],
                        m * _df[col],
                        left=m * _df[self.BAR_COLUMNS[:i]].sum(axis=1) + m * 0.02 * max_width,
                        color=color,
                        height=0.7,
                        linewidth=0,
                    )
            ax.scatter(
                [m * max_width * 0.955] * len(_df),
                -1 * _df["idx"],
                s=400,
                linewidths=1,
                c=_df["pos_color"],
                edgecolor=self.textcolor,
            )
            for _, r in _df.iterrows():
                ax.text(
                    m * max_width * 0.955,
                    -1 * r["idx"],
                    r["position"],
                    color=self.textcolor,
                    ha="center",
                    va="center",
                    fontsize=10,
                    fontproperties=font_normal.prop,
                )
                ax.text(
                    m * (max_width * 0.90),
                    -1 * r["idx"],
                    self.name_format(r["player_name"]),
                    color=self.textcolor,
                    ha="right" if m == 1 else "left",
                    va="center",
                    fontsize=12,
                    fontproperties=font_normal.prop,
                )
                ax.text(
                    m * r[self.TOTAL_COLUMN] + m * 0.04 * max_width,
                    -1 * r["idx"],
                    self._format_total(r[self.TOTAL_COLUMN]),
                    color="black",
                    ha="left" if m == 1 else "right",
                    va="center",
                    fontsize=10,
                    fontproperties=font_normal.prop,
                    bbox=dict(
                        facecolor="ivory",
                        alpha=1,
                        edgecolor="black",
                        boxstyle="round,pad=0.2",
                    ),
                )
            if self.UNDERBAR_COLUMN:
                topx.barh(
                    -1 * _df["idx"] - 0.35,
                    m * _df[self.UNDERBAR_COLUMN],
                    color=self.underbar_color,
                    left=m * 0.02 * max_width_secondary,
                    height=-0.1,
                    zorder=2,
                    align="edge",
                )

        ax.set_xbound(-max_width * 1.003, max_width * 1.003)
        if self.UNDERBAR_COLUMN:
            topx.set_xbound(-max_width_secondary, max_width_secondary)
        ax.set_ybound(min(-11, -max(home_team_df.shape[0], away_team_df.shape[0])), 0.5)
        topx.set_ybound(min(-11, -max(home_team_df.shape[0], away_team_df.shape[0])), 0.5)

    @staticmethod
    def name_format(name):
        name = name.split(" ")
        if len(name) == 1:
            return name[0].title()
        if len(name) == 2:
            return name[0][0].title() + ". " + name[1].title()
        else:
            return "".join([n[0].title() for n in name])

    @staticmethod
    def format_position(position):
        if position == "LB" or position == "RB":
            return "FB"
        if position in ["CDM", "CAM"] or (len(position) == 3 and position[0] in ["L", "R"]):
            return position[1:]
        if position == "RCDM" or position == "LCDM":
            return "DM"
        if position == "RCAM" or position == "LCAM":
            return "AM"
        return position

    @staticmethod
    def get_position_color(position):
        if position in ["GK"]:
            return "violet"
        if position in ["CB", "FB", "WB"]:
            return "lightblue"
        if position in ["LM", "RM", "CM", "DM", "AM"]:
            return "darkorange"
        else:
            return "red"

    def _plot_endnote(self, ax: Axes):
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
        custom_lines = [Line2D([0], [0], color=c, lw=4) for c in self.bar_colors] + [
            Line2D([0], [0], color=self.underbar_color, lw=2)
        ]
        ax.legend(
            custom_lines,
            [c.replace("_", " ").title() for c in self.BAR_COLUMNS]
            + [self.UNDERBAR_COLUMN.replace("_", " ").title()],
            facecolor=self.facecolor,
            edgecolor=self.facecolor,
            labelcolor=self.textcolor,
            loc="center left",
        )

        img = get_ball_logo2()
        size = img.size
        width = size[0] / size[1] * get_aspect(ax)

        logo_ax = ax.inset_axes((1.04 - width, 0, width, 1))
        logo_ax.axis("off")
        logo_ax.imshow(img, alpha=1)
        if self.EXPLAIN_TEXT:
            ax.text(
                self.EXPLAIN_TEXT_PLACEMENT,
                0.5,
                self.EXPLAIN_TEXT,
                va="center",
                ha="left",
                size=8,
                color=self.textcolor,
                fontproperties=font_italic.prop,
            )

    def _plot_title(self, data: pd.DataFrame, ax: Axes, fig: Figure):
        # date = dt.datetime.strptime(data["match_date"].iloc[0], "%Y-%m-%d")
        date = data["match_date"].iloc[0]
        home_score = data["home_score"].iloc[0]
        away_score = data["away_score"].iloc[0]
        home_team = data["home_team"].iloc[0]
        away_team = data["away_team"].iloc[0]
        league = data["decorated_league_name"].iloc[0]
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
        max_team_length = max(len(home_team), len(away_team))
        fontsize = 18
        if max_team_length >= 17:
            fontsize = 17
        if max_team_length >= 18:
            fontsize = 16
        if max_team_length >= 19:
            fontsize = 15
        if max_team_length >= 21:
            fontsize = 14
        if max_team_length >= 22:
            fontsize = 13

        ax.text(
            0.07,
            0.5,
            f"{home_team}",
            color=self.textcolor,
            va="center",
            ha="left",
            fontproperties=font_normal.prop,
            fontsize=fontsize,
        )
        ax.text(
            0.93,
            0.5,
            f"{away_team}",
            color=self.textcolor,
            va="center",
            ha="right",
            fontproperties=font_normal.prop,
            fontsize=fontsize,
        )
        ax.text(
            0.5,
            0.20,
            f"{data['decorated_league_name'].iloc[0]}",
            color=self.second_textcolor,
            va="center",
            ha="center",
            fontproperties=font_normal.prop,
            fontsize=14,
        )
        home_img = McLachBotBadgeService().team_badge(
            league, data.loc[data["is_home_team"] == True, "team"].iloc[0]
        )
        away_img = McLachBotBadgeService().team_badge(
            league, data.loc[data["is_home_team"] == False, "team"].iloc[0]
        )
        ax.text(
            0.5,
            -0.3,
            self.TITLE,
            color=self.textcolor,
            va="center",
            ha="center",
            fontproperties=font_bold.prop,
            fontsize=16,
        )
        ax2 = ax.inset_axes((-0.03, 0.105, get_aspect(ax) * 0.79, 0.79))
        ax2.imshow(home_img)
        ax2.axis("off")
        ax3 = ax.inset_axes((1.03 - get_aspect(ax) * 0.79, 0.105, get_aspect(ax) * 0.79, 0.79))
        ax3.imshow(away_img)
        ax3.axis("off")


class BallProgressionButterflyDashboard(ButterflyDashboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bar_colors = ["#e66100", "#5d3a9b"]

    TOTAL_COLUMN = "progressive_distance"
    BAR_COLUMNS = ["progressive_pass_distance", "progressive_carry_distance"]
    UNDERBAR_COLUMN = "progressive_distance_per_touch"
    TITLE = "Ball Progression Distances"
    EXPLAIN_TEXT = "Progressive Distance Per Touch\nis on a different scale.  It's useful\nto compare players to each other only"

    @property
    def datasource_name(self) -> str:
        return "ball_progression_butterfly"


class ExpectedGoalContributionsButterflyDashboard(ButterflyDashboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bar_colors = ["#574B60", "#EF767A"]

    TOTAL_COLUMN = "expected_goal_contributions"
    BAR_COLUMNS = ["non_penalty_expected_goals", "expected_assists"]
    UNDERBAR_COLUMN = "expected_goal_contributions_per_touch"
    TITLE = "Expected Goal Contributions"
    EXPLAIN_TEXT = "Expected Goal Contributions Per\nTouch is on a different scale.  It's\nuseful to compare players to each\nother only"
    EXPLAIN_TEXT_PLACEMENT = 0.55

    @property
    def datasource_name(self) -> str:
        return "expected_goal_contributions_butterfly"

    def _format_total(self, n: float):
        return f"{n:.2f}"


class ChanceCreationButterflyDashboard(ButterflyDashboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bar_colors = ["#DCB8CB", "#3A7D44", "#181D27"]

    TOTAL_COLUMN = "successful_actions_into_box"
    BAR_COLUMNS = [
        "crosses_completed_into_the_box",
        "open_play_passes_completed_into_the_box",
        "carries_into_the_box",
    ]
    UNDERBAR_COLUMN = "successful_deliveries_into_penalty_box"

    TITLE = "Successful Deliveries Into Penalty Box"
    EXPLAIN_TEXT = "Expected Deliveries Per Touch\nis on a different scale.  It's useful\nto compare players to each other only"
    EXPLAIN_TEXT_PLACEMENT = 0.6

    @property
    def datasource_name(self) -> str:
        return "chance_creation_butterfly"


class DuelsButterflyDashboard(ButterflyDashboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bar_colors = ["#D2CCA1", "#757780"]

    TOTAL_COLUMN = "total_duels_won"
    BAR_COLUMNS = [
        "ground_duels_won",
        "aerial_duels_won",
    ]
    UNDERBAR_COLUMN = "duel_win_percentage"

    TITLE = "Duels Won"

    @property
    def datasource_name(self) -> str:
        return "duels_butterfly"
