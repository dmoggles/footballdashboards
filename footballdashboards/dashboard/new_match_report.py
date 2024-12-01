import pandas as pd
import numpy as np
from typing import List, Dict, Any
from footballmodels.opta.actions import (
    is_kickoff,
    assign_possession_team_id,
    ppda_qualifying_defensive_actions,
    ppda_qualifying_passes,
)
from footballmodels.opta.aggregation.team_aggregation import (
    get_team_aggregation_2,
    possession_operations,
)
from footballmodels.opta.event_type import EventType
from footballdashboards.helpers.mplsoccer_helpers import bin_statistic
from matplotlib.figure import Figure

from matplotlib import patches as mpatches
from matplotlib import path as mpath
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.helpers import fonts
from matplotlib.axes import Axes
from mplsoccer.scatterutils import scatter_football
from mpl_pe_fancy_bar import BarToRoundBar
import mpl_visual_context.patheffects as pe
from mplsoccer.pitch import Pitch, VerticalPitch
import matplotlib.colors as mcolors
import requests
from footballmodels.opta.functions import col_get_qualifier_value
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService
from footballdashboards.helpers.mclachbot_helpers import TeamColorHelper
from footballdashboards.helpers.data_helpers import extract_names_sorted_by_position
from footballdashboards.helpers.formatters import smartest_name_formatter_yet
from footballmodels.opta.functions import col_has_qualifier

# from footballmodels.opta.actions import assi
from footballmodels.opta.distance import progressive_distance as pd_f
from footballmodels.opta.actions import (
    ground_duels_won,
    aerial_duels_won,
    in_attacking_box,
    open_play_box_entry,
)

from footballmodels.opta.distance import (
    distance,
    MIDDLE_GOAL_COORDS,
    TOP_GOAL_COORDS,
    BOTTOM_GOAL_COORDS,
)
import highlight_text as ht
from footballdashboards.helpers.mclachbot_helpers import get_ball_logo2
from footballdashboardsdata.funnels.funnel_api import get_dataframe_for_match


def color_name_to_hex(color_name):
    try:
        # Convert color name to hex using matplotlib's color dictionary
        return mcolors.CSS4_COLORS[color_name]
    except KeyError:
        return "Color name not recognized. Please use a valid Matplotlib color name."


def hex_to_rgb(hex_code):
    # Remove the '#' if present
    hex_code = hex_code.lstrip("#")

    # Convert each pair of hex characters to decimal (R, G, B)
    return tuple(int(hex_code[i : i + 2], 16) / 256 for i in (0, 2, 4))


def get_xthreat_grid() -> List[List[float]]:
    """
    Retrieve the xthread grid from the web
    """

    r = requests.get("https://karun.in/blog/data/open_xt_12x8_v1.json")
    if r.status_code != 200:
        raise Exception("Could not retrieve xthreat grid")
    return r.json()


def generate_match_stats(data):
    data = data[~data["event_type"].isin([EventType.OffsideGiven])].copy()
    data["kickoff"] = is_kickoff(data)
    possession_id_dict = data.groupby("possession_number").apply(
        lambda x: assign_possession_team_id(x)
    )

    data["possession_owner"] = data["possession_number"].map(possession_id_dict)
    poss_data = data.groupby(["season", "competition", "matchId", "possession_number"]).apply(
        possession_operations
    )
    poss_data.index = poss_data.index.droplevel(4)
    data["ppda_a"] = ppda_qualifying_defensive_actions(data)
    data["ppda_p"] = ppda_qualifying_passes(data)

    team_data = get_team_aggregation_2(data, poss_data)
    home_away = data.groupby(["teamId"]).agg({"is_home_team": "first"}).to_dict()["is_home_team"]
    team_data["is_home_team"] = team_data.index.get_level_values(3).map(home_away)
    for teamId in data["teamId"].unique():
        team_data.loc[team_data.index.get_level_values(3) == teamId, "ppda"] = data.loc[
            data["teamId"] == teamId, "ppda_a"
        ].sum()
    return team_data


def get_match_stat_history(league, conn):
    query = f"""
    

    SELECT matchId, teamId, metric_name, value FROM agg.team_aggregations A
        JOIN
        agg.team_agg_metric_definitions B
        ON A.metricId=B.id
        WHERE A.competition = '{league}'
        AND B.metric_name IN (
            
            'ppda_qualifying_passes',
            'ppda_qualifying_defensive_actions',
            'circulation',
            'fast_break',
            'build_up_possession',
            'pass_progressive_distance',
            'pass_total_distance',
            'start_possession_distance',
            'end_possession_distance',
            'buildup_possession',
            'pct_gained',
            'open_play_box_entry',
            'second_ball_wins'
    )        

    """
    data = conn.query(query)
    data = data.pivot(index=["matchId", "teamId"], columns="metric_name", values="value").dropna()

    return data


def create_layout(facecolor="white"):
    fig = Figure(figsize=(20, 18), facecolor=facecolor)
    axes = fig.subplot_mosaic(
        [
            # ['top','top','top'],
            ["left_pn", "header", "right_pn"],
            ["left_pn", "gameflow", "right_pn"],
            ["left_pn", "heatmap_", "right_pn"],
            ["left_stats", "match_stats", "right_stats"],
            ["left_stats", "shot_map", "right_stats"],
            ["bottom", "bottom", "bottom"],
        ],
        width_ratios=[1, 1.3, 1],
        height_ratios=[2, 2, 4, 2.5, 2.5, 1],
    )
    fig.subplots_adjust(wspace=0.1, hspace=0.1)

    possession_ax = axes["heatmap_"].inset_axes([0, 0, 0.05, 1])
    heatmap_ax = axes["heatmap_"].inset_axes([0.05, 0, 0.9, 1])
    field_tilt_ax = axes["heatmap_"].inset_axes([0.95, 0, 0.05, 1])
    axes["heatmap_"].axis("off")
    axes["possession"] = possession_ax
    axes["heatmap"] = heatmap_ax
    axes["field_tilt"] = field_tilt_ax
    return fig, axes


class RoundedHelpers:
    @staticmethod
    def draw_unfilled_circle(ax, x, y, radius, color="black", filled=False):
        scale = 1 / get_aspect(ax)
        path_data = [
            (mpath.Path.MOVETO, [x, y + radius * scale]),
            (mpath.Path.CURVE3, [x + radius, y + radius * scale]),
            (mpath.Path.CURVE3, [x + radius, y]),
            (mpath.Path.CURVE3, [x + radius, y - radius * scale]),
            (mpath.Path.CURVE3, [x, y - radius * scale]),
            (mpath.Path.CURVE3, [x - radius, y - radius * scale]),
            (mpath.Path.CURVE3, [x - radius, y]),
            (mpath.Path.CURVE3, [x - radius, y + radius * scale]),
            (mpath.Path.CURVE3, [x, y + radius * scale]),
            (mpath.Path.CLOSEPOLY, [x, y + radius * scale]),
        ]

        codes, verts = zip(*path_data)
        path = mpath.Path(verts, codes)
        patch = mpatches.PathPatch(
            path, facecolor="none" if not filled else color, edgecolor=color, lw=2
        )
        ax.add_patch(patch)

    @staticmethod
    def draw_semifilled_circle(ax, x, y, radius, color="black", filled_side="left"):
        scale = 1 / get_aspect(ax)
        path_data_1 = [
            (mpath.Path.MOVETO, [x, y + radius * scale]),
            (mpath.Path.CURVE3, [x + radius, y + radius * scale]),
            (mpath.Path.CURVE3, [x + radius, y]),
            (mpath.Path.CURVE3, [x + radius, y - radius * scale]),
            (mpath.Path.CURVE3, [x, y - radius * scale]),
        ]
        path_data_2 = [
            (mpath.Path.MOVETO, [x, y + radius * scale]),
            (mpath.Path.CURVE3, [x - radius, y + radius * scale]),
            (mpath.Path.CURVE3, [x - radius, y]),
            (mpath.Path.CURVE3, [x - radius, y - radius * scale]),
            (mpath.Path.CURVE3, [x, y - radius * scale]),
        ]
        codes, verts = zip(*path_data_1)
        path = mpath.Path(verts, codes)
        patch = mpatches.PathPatch(
            path, facecolor="none" if filled_side == "left" else color, edgecolor=color, lw=2
        )
        ax.add_patch(patch)
        codes, verts = zip(*path_data_2)
        path = mpath.Path(verts, codes)
        patch = mpatches.PathPatch(
            path, facecolor="none" if filled_side == "right" else color, edgecolor=color, lw=2
        )
        ax.add_patch(patch)

    @staticmethod
    def draw_semirounded_box(ax, x, y, width, height, facecolor, edgecolor):
        Path = mpath.Path
        offset = height / 2
        x_data_range = ax.get_xlim()[1] - ax.get_xlim()[0]
        y_data_range = ax.get_ylim()[1] - ax.get_ylim()[0]

        offset = offset / (y_data_range / x_data_range)

        path_data = [
            (Path.MOVETO, [x - width, y - height]),
            (Path.CURVE4, [x - width - offset, y - height]),
            (Path.CURVE4, [x - width - offset, y + height]),
            (Path.CURVE4, [x - width, y + height]),
            (Path.LINETO, [x + width, y + height]),
            (Path.CURVE4, [x + width + offset, y + height]),
            (Path.CURVE4, [x + width + offset, y - height]),
            (Path.CURVE4, [x + width, y - height]),
            (Path.CLOSEPOLY, [x - width, y - height]),
        ]
        codes, verts = zip(*path_data)
        path = mpath.Path(verts, codes)
        patch = mpatches.PathPatch(
            path, facecolor=facecolor, edgecolor=edgecolor, lw=1, transform=ax.transAxes
        )
        ax.add_patch(patch)


class MatchStats:

    @staticmethod
    def get_rank(match_data, context_data, metric_name):
        context_data["ppda"] = context_data["ppda_qualifying_defensive_actions"]

        match_id = match_data.index.get_level_values(2)[0]
        if match_id not in context_data.index.get_level_values(0):
            full_data = pd.concat(
                [context_data, match_data.reset_index().set_index(["matchId", "teamId"])]
            )
        else:
            full_data = context_data
        reverse = ["start_possession_distance"]
        full_data["rank"] = full_data[metric_name].rank(
            ascending=metric_name not in reverse, method="average", pct=True
        )
        return full_data.loc[match_id, "rank"]

    @staticmethod
    def draw_team_stats_labels(ax):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        for i, label in enumerate(
            [
                "Start distance",
                "Box Entries",
                "2nd Ball Wins",
                "Build-ups",
                "Fast breaks",
                "High press",
            ]
        ):
            ax.text(
                0.5,
                1 - (i + 1) * 1 / 7,
                label,
                ha="center",
                va="center",
                fontsize=12,
                color="black",
                fontproperties=fonts.font_normal.prop,
                weight="bold",
            )

    @staticmethod
    def draw_team_stat_values(ax, match_data, context_data, team_colors, bg_color):
        match_data = match_data.sort_values("is_home_team", ascending=False)
        context_data["pct_gained"] = 100 * context_data["pct_gained"]
        match_data["pct_gained"] = 100 * match_data["pct_gained"]
        context_data["circulation"] = 100 * context_data["circulation"]
        match_data["circulation"] = 100 * match_data["circulation"]
        for i, col in enumerate(
            [
                "start_possession_distance",
                "open_play_box_entry",
                "second_ball_wins",
                "buildup_possession",
                "fast_break",
                "ppda",
            ]
        ):
            rank_df = MatchStats.get_rank(match_data, context_data, col)
            for ha in [1, 0]:
                team_id = match_data[match_data["is_home_team"] == ha].index.get_level_values(3)[0]
                side = ((1 - ha) * 2) - 1
                x = 0.5 + 0.15 * side
                v = int(match_data.loc[match_data["is_home_team"] == ha, col].values[0])
                v_str = f"{v:.0f}"
                if col in ["circulation", "pct_gained"]:
                    v_str = f"{v:.0f}%"
                bigger = (
                    match_data.loc[match_data["is_home_team"] == ha, col].values[0]
                    > match_data.loc[match_data["is_home_team"] != ha, col].values[0]
                )
                if col == "start_possession_distance":
                    bigger = not bigger
                if bigger:
                    font_c = bg_color
                else:
                    font_c = "black"
                ax.text(
                    x,
                    1 - (i + 1) * 1 / 7,
                    v_str,
                    ha="center",
                    va="center",
                    fontsize=12,
                    color=font_c,
                    fontproperties=fonts.font_normal.prop,
                    weight="bold",
                )
                if bigger:
                    RoundedHelpers.draw_semirounded_box(
                        ax,
                        x,
                        1 - (i + 1) * 1 / 7,
                        0.02,
                        0.05,
                        facecolor=team_colors[ha],
                        edgecolor=team_colors[ha],
                    )
                else:
                    RoundedHelpers.draw_semirounded_box(
                        ax,
                        x,
                        1 - (i + 1) * 1 / 7,
                        0.02,
                        0.05,
                        facecolor=bg_color,
                        edgecolor=team_colors[ha],
                    )
                rank = rank_df.loc[team_id]
                for j in range(0, 5):
                    if j == 4 and rank > 0.95:
                        RoundedHelpers.draw_unfilled_circle(
                            ax,
                            0.5 + (0.25 * side) + (side * 0.05 * j),
                            1 - (i + 1) * 1 / 7,
                            0.05 * get_aspect(ax),
                            color=team_colors[ha],
                            filled=True,
                        )
                        continue
                    if rank > (j + 1) * 0.2:

                        RoundedHelpers.draw_unfilled_circle(
                            ax,
                            0.5 + (0.25 * side) + (side * 0.05 * j),
                            1 - (i + 1) * 1 / 7,
                            0.05 * get_aspect(ax),
                            color=team_colors[ha],
                            filled=True,
                        )
                    elif rank > (j + 0.5) * 0.2:
                        RoundedHelpers.draw_semifilled_circle(
                            ax,
                            0.5 + (0.25 * side) + (side * 0.05 * j),
                            1 - (i + 1) * 1 / 7,
                            0.05 * get_aspect(ax),
                            color=team_colors[ha],
                            filled_side="right" if ha == 1 else "left",
                        )
                    else:
                        RoundedHelpers.draw_unfilled_circle(
                            ax,
                            0.5 + (0.25 * side) + (side * 0.05 * j),
                            1 - (i + 1) * 1 / 7,
                            0.05 * get_aspect(ax),
                            color=team_colors[ha],
                            filled=False,
                        )

    def match_stats_ax(ax, match_data, context_data, visualisation_arguments):
        team_colors = {
            1: visualisation_arguments["home_team_color"],
            0: visualisation_arguments["away_team_color"],
        }
        MatchStats.draw_team_stats_labels(ax)
        MatchStats.draw_team_stat_values(
            ax, match_data, context_data, team_colors, visualisation_arguments["facecolor"]
        )


class GameFlow:
    @staticmethod
    def assign_xthreat_to_events(data: pd.DataFrame) -> pd.DataFrame:
        """
        Assign xthreat values to each event in the data
        """
        xthreat_grid = get_xthreat_grid()
        xt_idx_x = pd.cut(data["x"], bins=np.linspace(0, 100, 13), labels=range(12)).fillna(0)
        xt_idx_y = pd.cut(data["y"], bins=np.linspace(0, 100, 9), labels=range(8)).fillna(0)
        data["xthreat"] = [xthreat_grid[y][x] for x, y in zip(xt_idx_x, xt_idx_y)]
        return data

    @staticmethod
    def bin_data_into_minutes(data: pd.DataFrame, max_xthreat_value: float) -> pd.DataFrame:
        """
        Bin the data into periods, minutes and teams and cap at the maximum xthreat value
        """
        data["is_goal"] = data["event_type"] == EventType.Goal
        agg_data = (
            data.groupby(["period", "minute", "team", "is_home_team"])
            .agg({"xthreat": "max", "is_goal": "sum"})
            .reset_index()
            .rename(columns={"is_goal": "goals"})
        )
        agg_data["xthreat"] = agg_data["xthreat"].clip(0, max_xthreat_value)
        return agg_data

    @staticmethod
    def fill_missing_minutes(data: pd.DataFrame) -> pd.DataFrame:
        """
        Fill in missing minutes in the data
        """
        max_minutes_in_period = data.groupby("period")["minute"].max().to_dict()
        home_away_teams = data.groupby("team")["is_home_team"].first().to_dict()
        periods = data["period"].unique()
        teams = data["team"].unique()
        full_data = []
        for period in periods:
            for minute in (
                range(0, max_minutes_in_period[period] + 1)
                if period == 1
                else range(45, max_minutes_in_period[period] + 1)
            ):
                for team in teams:
                    if (
                        len(
                            data[
                                (data["period"] == period)
                                & (data["minute"] == minute)
                                & (data["team"] == team)
                            ]
                        )
                        == 0
                    ):
                        full_data.append(
                            {
                                "period": period,
                                "minute": minute,
                                "team": team,
                                "xthreat": 0,
                                "goals": 0,
                            }
                        )
        full_data = pd.DataFrame(full_data)

        full_data = (
            pd.concat([data, full_data])
            .sort_values(["period", "minute", "team"])
            .reset_index(drop=True)
        )
        full_data["is_home_team"] = full_data["team"].map(home_away_teams)
        return full_data

    @staticmethod
    def calculate_xthreat_ewma(data: pd.DataFrame, minute_rolling_window: float) -> pd.DataFrame:
        """
        Calculate the exponentially weighted moving average of the xthreat values
        """

        def _compute_ewma(x: pd.Series, minute_rolling_window: float) -> pd.Series:
            alpha = 2 / (minute_rolling_window + 1)
            lagging = x.ewm(alpha=alpha).mean().values
            leading = x.iloc[::-1].ewm(alpha=alpha).mean().iloc[::-1].values
            avg = np.concatenate([leading[:5], (leading[5:-5] + lagging[5:-5]) / 2, lagging[-5:]])

            return pd.Series(avg, index=x.index)

        data["xthreat"] = data.groupby(["team", "period", "is_home_team"])["xthreat"].transform(
            lambda x: _compute_ewma(x, minute_rolling_window)
        )

        return data

    @staticmethod
    def setup_central_timeline(ax, data, args):
        """
        This function will create the time line in the middle of the gameflow chart
        """
        first_period_labels = [1, 15, 30, 45]
        second_period_labels = [60, 75, 90]

        first_period_idx = [
            data.loc[(data["period"] == 1) & (data["minute"] == minute), "time"].values[0]
            for minute in first_period_labels
        ]
        second_period_idx = [
            data.loc[(data["period"] == 2) & (data["minute"] == minute), "time"].values[0]
            for minute in second_period_labels
        ]
        for idx, label in zip(
            first_period_idx + second_period_idx, first_period_labels + second_period_labels
        ):
            ax.text(
                idx, 0, f"{label}'", ha="center", va="center", fontsize=10, color=args["text_color"]
            )

        GameFlow.shade_extra_time(ax, data)

    @staticmethod
    def shade_extra_time(ax: Axes, data: pd.DataFrame):
        """
        Shade the extra time on the time line
        """
        first_period__extra_time_range = (
            data.loc[(data["period"] == 1) & (data["minute"] == 45), "time"].values[0],
            data.loc[data["period"] == 1, "time"].max(),
        )
        second_period__extra_time_range = (
            data.loc[(data["period"] == 2) & (data["minute"] == 90), "time"].values[0],
            data.loc[data["period"] == 2, "time"].max(),
        )

        ax.fill_betweenx(
            [-0.02, 0.02], *first_period__extra_time_range, color="lightgrey", alpha=0.5
        )
        ax.fill_betweenx(
            [-0.02, 0.02], *second_period__extra_time_range, color="lightgrey", alpha=0.5
        )

    @staticmethod
    def setup_axis(ax: Axes, data: pd.DataFrame):
        """
        Set the axis dimention and turn off the default ticks and axis display

        """

        # set the x-axis limits and remove the default ticks
        ax.set_xlim(-0.5, data["time"].max() + 0.5)
        max_xthreat = data["xthreat"].abs().max() + 0.08  # space for balls to indicate goals
        ax.set_ylim(min(max_xthreat, -0.18), max(max_xthreat, 0.18))
        ax.axis("off")

    @staticmethod
    def draw_gameflow(ax: Axes, data: pd.DataFrame, args: Dict[str, Any]):
        """
        Draw the gameflow chart bars
        """

        patheffects_top = [BarToRoundBar() | pe.AlphaGradient("0.2 ^ 1")]
        patheffects_bottom = [BarToRoundBar() | pe.AlphaGradient("1 ^ 0.2")]

        home_data = data[data["is_home_team"] == 1]
        away_data = data[data["is_home_team"] == 0]
        home_team = home_data["team"].values[0]
        away_team = away_data["team"].values[0]

        # Plot the data
        bars_tops = ax.bar(
            home_data["time"],
            home_data["xthreat"],
            color=args["home_team_color"],
            label=home_team,
            bottom=0.02,
        )
        bars_bottom = ax.bar(
            away_data["time"],
            away_data["xthreat"],
            color=args["away_team_color"],
            label=away_team,
            bottom=-0.02,
        )
        for bar in bars_tops:

            bar.set_path_effects(patheffects_top)
        for bar in bars_bottom:
            bar.set_path_effects(patheffects_bottom)

    @staticmethod
    def place_goals(ax: Axes, data: pd.DataFrame, args: Dict[str, Any]):
        """
        Place the balls that represent on the gameflow chart.
        If more than one goal is scored at any minute, stack the balls diagonally
        on top of each other
        """
        home_goals = data[(data["is_home_team"] == 1) & (data["goals"] > 0)]
        away_goals = data[(data["is_home_team"] == 0) & (data["goals"] > 0)]

        for i, r in home_goals.iterrows():
            n_goals = r["goals"]
            for k in range(n_goals, 0, -1):
                scatter_football(
                    r["time"] + k * 0.3,
                    0.15 + k * 0.01,
                    ax=ax,
                    s=55,
                    edgecolors=args["home_team_color"],
                )
        for i, r in away_goals.iterrows():
            n_goals = r["goals"]
            for k in range(n_goals, 0, -1):
                scatter_football(
                    r["time"] + k * 0.3,
                    -0.15 - k * 0.01,
                    ax=ax,
                    s=55,
                    edgecolors=args["away_team_color"],
                )
        # scatter_football(away_goals['time'], [-0.135]*len(away_goals), ax=ax, s=55, edgecolors=args['away_team_color'])

    @staticmethod
    def fancy_gameflow_chart(ax: Axes, data: pd.DataFrame, args: Dict[str, Any]):
        """
        Create a fancy gameflow chart
        """
        data = data.copy()
        # simplify by converting the period and minute into a single time value
        data["time"] = data.apply(
            lambda x: (
                x["minute"]
                if x["period"] == 1
                else x["minute"] + data.loc[data["period"] == 1, "minute"].max() + 1 - 45
            ),
            axis=1,
        )
        data = data.sort_values("time")
        data["xthreat"] = data.apply(
            lambda x: x["xthreat"] if x["is_home_team"] == 1 else -x["xthreat"], axis=1
        )
        GameFlow.setup_axis(ax, data)
        GameFlow.setup_central_timeline(ax, data, args)
        GameFlow.draw_gameflow(ax, data, args)
        GameFlow.place_goals(ax, data, args)

    @staticmethod
    def process(raw_data: pd.DataFrame, ax: Axes, args: Dict[str, Any]):
        """
        Process the raw data and draw the gameflow chart
        """
        processed_data = (
            raw_data.copy()
            .pipe(GameFlow.assign_xthreat_to_events)
            .pipe(GameFlow.bin_data_into_minutes, max_xthreat_value=0.2)
            .pipe(GameFlow.fill_missing_minutes)
            .pipe(GameFlow.calculate_xthreat_ewma, minute_rolling_window=5)
        )

        GameFlow.fancy_gameflow_chart(ax, processed_data, args)


class Heatmap:
    @staticmethod
    def heatmap_transform_data(data):
        data = data.copy()
        applicable_events = [
            EventType.Aerial,
            EventType.Goal,
            EventType.BallRecovery,
            EventType.BallTouch,
            EventType.BlockedPass,
            EventType.Challenge,
            EventType.Clearance,
            EventType.Dispossessed,
            EventType.GoodSkill,
            EventType.Interception,
            EventType.MissedShots,
            EventType.Pass,
            EventType.SavedShot,
            EventType.ShotOnPost,
            EventType.Tackle,
            EventType.TakeOn,
        ]
        data = data[data["event_type"].isin(applicable_events)]
        data["possession_side"] = data["is_home_team"].apply(lambda x: 1 if x == 1 else -1)
        data["x"] = data.apply(
            lambda x: x["x"] if x["possession_side"] == 1 else 100 - x["x"], axis=1
        )
        data["y"] = data.apply(
            lambda x: x["y"] if x["possession_side"] == 1 else 100 - x["y"], axis=1
        )
        return data

    @staticmethod
    def generate_colormap(home_color, away_color):
        if home_color[0] != "#":
            home_color = color_name_to_hex(home_color)
        if away_color[0] != "#":
            away_color = color_name_to_hex(away_color)
        home_rgb = hex_to_rgb(home_color)
        away_rgb = hex_to_rgb(away_color)
        return mcolors.LinearSegmentedColormap.from_list(
            "custom",
            [
                (0, (away_rgb[0], away_rgb[1], away_rgb[2], 0.9)),
                (0.499, (away_rgb[0], away_rgb[1], away_rgb[2], 0.0)),
                (0.501, (home_rgb[0], home_rgb[1], home_rgb[2], 0.0)),
                (1, (home_rgb[0], home_rgb[1], home_rgb[2], 0.9)),
            ],
        )

    @staticmethod
    def process(ax, data, visualisation_parameters):
        data_transformed = Heatmap.heatmap_transform_data(data)
        pitch = Pitch(
            pitch_type="opta",
            pitch_color="oldlace",
            line_color=visualisation_parameters["pitch_line_color"],
            linewidth=1,
        )
        bins = bin_statistic(
            data_transformed["x"],
            data_transformed["y"],
            values=data_transformed["possession_side"],
            statistic="sum",
            bins=(18, 12),
            dim=pitch.dim,
            gaussian_filter_value=1,
            zoom_value=10,
        )
        max_abs_value = max([abs(bins["statistic"].min()), bins["statistic"].max()])
        cmap = Heatmap.generate_colormap(
            visualisation_parameters["home_team_color"], visualisation_parameters["away_team_color"]
        )
        pitch.draw(ax=ax)
        pitch.heatmap(
            bins,
            edgecolors="white",
            ax=ax,
            cmap=cmap,
            lw=0,
            vmin=-max_abs_value,
            vmax=max_abs_value,
        )


class ShotMap:
    @staticmethod
    def setup_shot_maps(ax, visualisation_parameters):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        left_side = ax.inset_axes([0, 0, 0.5, 1])

        right_side = ax.inset_axes([0.5, 0, 0.5, 1])

        pitch_left = VerticalPitch(
            pitch_type="opta",
            half=True,
            pitch_color=visualisation_parameters["facecolor"],
            line_color=visualisation_parameters["pitch_line_color"],
            linewidth=1,
        )
        pitch_right = VerticalPitch(
            pitch_type="opta",
            half=True,
            pitch_color=visualisation_parameters["facecolor"],
            line_color=visualisation_parameters["pitch_line_color"],
            linewidth=1,
        )
        pitch_left.draw(ax=left_side)
        pitch_right.draw(ax=right_side)
        right_side.set_xlim(15, 85)
        right_side.set_ylim(60, 101)
        left_side.set_xlim(15, 85)
        left_side.set_ylim(60, 101)
        return left_side, pitch_left, right_side, pitch_right

    @staticmethod
    def plot_shots(
        data, left_side_ax, pitch_left, right_side_ax, pitch_right, visualisation_parameters
    ):
        home_shots = data[
            (
                data["event_type"].isin(
                    [EventType.ShotOnPost, EventType.SavedShot, EventType.MissedShots]
                )
            )
            & (data["is_home_team"] == 1)
        ].copy()
        away_shots = data[
            (
                data["event_type"].isin(
                    [EventType.ShotOnPost, EventType.SavedShot, EventType.MissedShots]
                )
            )
            & (data["is_home_team"] == 0)
        ].copy()
        home_goals = data[
            (data["event_type"] == EventType.Goal) & (data["is_home_team"] == 1)
        ].copy()
        away_goals = data[
            (data["event_type"] == EventType.Goal) & (data["is_home_team"] == 0)
        ].copy()
        for tbl in [home_shots, away_shots, home_goals, away_goals]:
            tbl["size"] = np.power(
                visualisation_parameters["min_xg_size"]
                + (
                    np.minimum(tbl["xG"], visualisation_parameters["max_xg_value"])
                    / visualisation_parameters["max_xg_value"]
                )
                * (
                    visualisation_parameters["max_xg_size"]
                    - visualisation_parameters["min_xg_size"]
                ),
                2,
            )
            tbl["y"] = 100 - tbl["y"]

        # print(home_shots[['x','xG','size']])
        pitch_left.scatter(
            home_shots["x"],
            home_shots["y"],
            s=home_shots["size"],
            color=(0, 0, 0, 0),
            edgecolors=visualisation_parameters["home_team_color"],
            ax=left_side_ax,
            zorder=2,
        )
        pitch_right.scatter(
            away_shots["x"],
            away_shots["y"],
            s=away_shots["size"],
            color=(0, 0, 0, 0),
            edgecolors=visualisation_parameters["away_team_color"],
            ax=right_side_ax,
            zorder=2,
        )
        pitch_left.scatter(
            home_goals["x"],
            home_goals["y"],
            s=home_goals["size"],
            color=visualisation_parameters["home_team_color"],
            ax=left_side_ax,
            zorder=3,
        )
        pitch_right.scatter(
            away_goals["x"],
            away_goals["y"],
            s=away_goals["size"],
            color=visualisation_parameters["away_team_color"],
            ax=right_side_ax,
            zorder=3,
        )
        home_goalmouth_y = (
            100
            - col_get_qualifier_value(home_goals, display_name="GoalMouthY").astype(float).values
        )
        pitch_left.lines(
            home_goals["x"],
            home_goals["y"],
            [100] * len(home_goals),
            home_goalmouth_y,
            color=visualisation_parameters["home_team_color"],
            ax=left_side_ax,
            lw=1,
        )
        away_goalmouth_y = (
            100
            - col_get_qualifier_value(away_goals, display_name="GoalMouthY").astype(float).values
        )
        pitch_right.lines(
            away_goals["x"],
            away_goals["y"],
            [100] * len(away_goals),
            away_goalmouth_y,
            color=visualisation_parameters["away_team_color"],
            ax=right_side_ax,
            lw=1,
        )

        home_xg = home_shots["xG"].sum() + home_goals["xG"].sum()
        away_xg = away_shots["xG"].sum() + away_goals["xG"].sum()
        if home_xg > away_xg:
            pitch_left.text(
                63,
                50,
                f"{home_xg:.2f} xG",
                ha="center",
                va="center",
                fontsize=10,
                color=visualisation_parameters["facecolor"],
                fontproperties=fonts.font_bold.prop,
                ax=left_side_ax,
            )
            RoundedHelpers.draw_semirounded_box(
                left_side_ax,
                0.5,
                3 / 40,
                0.1,
                0.05,
                facecolor=visualisation_parameters["home_team_color"],
                edgecolor=visualisation_parameters["home_team_color"],
            )
        else:
            pitch_left.text(
                63,
                50,
                f"{home_xg:.2f} xG",
                ha="center",
                va="center",
                fontsize=10,
                color="black",
                fontproperties=fonts.font_bold.prop,
                ax=left_side_ax,
            )
            RoundedHelpers.draw_semirounded_box(
                left_side_ax,
                0.5,
                3 / 40,
                0.1,
                0.05,
                facecolor=visualisation_parameters["facecolor"],
                edgecolor=visualisation_parameters["home_team_color"],
            )

        if away_xg > home_xg:
            pitch_right.text(
                63,
                50,
                f"{away_xg:.2f} xG",
                ha="center",
                va="center",
                fontsize=10,
                color=visualisation_parameters["facecolor"],
                fontproperties=fonts.font_bold.prop,
                ax=right_side_ax,
            )
            RoundedHelpers.draw_semirounded_box(
                right_side_ax,
                0.5,
                3 / 40,
                0.1,
                0.05,
                facecolor=visualisation_parameters["away_team_color"],
                edgecolor=visualisation_parameters["away_team_color"],
            )
        else:
            pitch_right.text(
                63,
                50,
                f"{away_xg:.2f} xG",
                ha="center",
                va="center",
                fontsize=10,
                color="black",
                fontproperties=fonts.font_bold.prop,
                ax=right_side_ax,
            )
            RoundedHelpers.draw_semirounded_box(
                right_side_ax,
                0.5,
                3 / 40,
                0.1,
                0.05,
                facecolor=visualisation_parameters["facecolor"],
                edgecolor=visualisation_parameters["away_team_color"],
            )

    def process(data, ax, visualisation_parameters):
        left_side, pitch_left, right_side, pitch_right = ShotMap.setup_shot_maps(
            ax, visualisation_parameters
        )
        ShotMap.plot_shots(
            data, left_side, pitch_left, right_side, pitch_right, visualisation_parameters
        )


class Header:

    def create_header(ax, data, visualisation_parameters):
        ax.axis("off")
        home_team = data[data["is_home_team"] == 1]["decorated_team_name"].values[0]
        away_team = data[data["is_home_team"] == 0]["decorated_team_name"].values[0]
        plain_home_name = data[data["is_home_team"] == 1]["team"].values[0]
        plain_away_name = data[data["is_home_team"] == 0]["team"].values[0]
        home_score = data["home_score"].values[0]
        away_score = data["away_score"].values[0]
        league = data["decorated_league_name"].values[0]
        plain_league = data["competition"].values[0]
        match_date = data["match_date"].values[0].strftime("%B %-d, %Y")
        ax.text(
            0.5,
            0.5,
            f"{home_score:.0f} - {away_score:.0f}",
            ha="center",
            va="center",
            fontsize=20,
            color="black",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            0.5,
            0.35,
            league,
            ha="center",
            va="center",
            fontsize=10,
            color="grey",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            0.5,
            0.25,
            match_date,
            ha="center",
            va="center",
            fontsize=10,
            color="grey",
            fontproperties=fonts.font_bold.prop,
        )
        aspect = get_aspect(ax)
        home_badge_ax = ax.inset_axes([0.2, 0.3, 0.1, 0.1 / aspect])
        away_badge_ax = ax.inset_axes([0.7, 0.3, 0.1, 0.1 / aspect])

        home_badge = McLachBotBadgeService().team_badge(plain_league, plain_home_name)
        away_badge = McLachBotBadgeService().team_badge(plain_league, plain_away_name)
        home_badge_ax.imshow(home_badge)
        away_badge_ax.imshow(away_badge)
        home_badge_ax.axis("off")
        away_badge_ax.axis("off")

        ax.text(
            0.25,
            0.1,
            home_team,
            ha="center",
            va="center",
            fontsize=10,
            color=visualisation_parameters["facecolor"],
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            0.75,
            0.1,
            away_team,
            ha="center",
            va="center",
            fontsize=10,
            color=visualisation_parameters["facecolor"],
            fontproperties=fonts.font_bold.prop,
        )
        RoundedHelpers.draw_semirounded_box(
            ax,
            0.25,
            0.1,
            0.15,
            0.05,
            facecolor=visualisation_parameters["home_team_color"],
            edgecolor=visualisation_parameters["home_team_color"],
        )
        RoundedHelpers.draw_semirounded_box(
            ax,
            0.75,
            0.1,
            0.15,
            0.05,
            facecolor=visualisation_parameters["away_team_color"],
            edgecolor=visualisation_parameters["away_team_color"],
        )


class SideBars:
    @staticmethod
    def agg_minutes(dataframe):
        seconds_dict = {}
        home = dataframe.loc[dataframe["is_home_team"] == True, "team"].iloc[0]
        away = dataframe.loc[dataframe["is_home_team"] == False, "team"].iloc[0]

        for i, g in dataframe.groupby("possession_number"):
            team = g["team"].iloc[0]
            seconds = g["match_seconds"].max() - g["match_seconds"].min()
            if team in seconds_dict:
                seconds_dict[team] += seconds
            else:
                seconds_dict[team] = seconds
        return (
            seconds_dict[home] / sum(seconds_dict.values()),
            seconds_dict[away] / sum(seconds_dict.values()),
        )

    @staticmethod
    def possession(ax, data, visualisation_parameters):
        possession = SideBars.agg_minutes(data)
        SideBars.side_bar(ax, possession, visualisation_parameters, "Possession", "left")

    @staticmethod
    def field_tilt(ax, data, visualisation_parameters):
        final_third_passes = data[(data["event_type"] == EventType.Pass) & (data["x"] > 66.6)]
        final_third_passes = final_third_passes.groupby("is_home_team").size()
        home_final_third_passes = final_third_passes.get(1, 0)
        away_final_third_passes = final_third_passes.get(0, 0)
        home_field_tilt = home_final_third_passes / (
            home_final_third_passes + away_final_third_passes
        )
        away_field_tilt = away_final_third_passes / (
            home_final_third_passes + away_final_third_passes
        )
        SideBars.side_bar(
            ax, (home_field_tilt, away_field_tilt), visualisation_parameters, "Field Tilt", "right"
        )

    @staticmethod
    def side_bar(ax, possession, visualisation_parameters, title, side):
        patheffects_top = [BarToRoundBar() | pe.AlphaGradient("0.5 ^ 1")]
        patheffects_bottom = [BarToRoundBar() | pe.AlphaGradient("1 ^ 0.5")]

        ax.set_ylim(-possession[1] - 0.06, possession[0] + 0.06)
        ax.set_xlim(0, 1)
        bar_top = ax.bar(
            0.5 if side == "left" else 0,
            possession[0],
            color=visualisation_parameters["home_team_color"],
            width=0.5,
            bottom=0.005,
            align="edge",
        )
        bar_bottom = ax.bar(
            0.5 if side == "left" else 0,
            -possession[1],
            color=visualisation_parameters["away_team_color"],
            width=0.5,
            bottom=-0.005,
            align="edge",
        )

        home_fig = f"{possession[0]*100:.0f}"
        away_fig = f"{possession[1]*100:.0f}"

        ax.text(
            0.75 if side == "left" else 0.25,
            0.025,
            home_fig,
            ha="center",
            va="center",
            fontsize=8,
            color="oldlace",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            0.75 if side == "left" else 0.25,
            -0.025,
            away_fig,
            ha="center",
            va="center",
            fontsize=8,
            color="oldlace",
            fontproperties=fonts.font_bold.prop,
        )
        bar_top[0].set_path_effects(patheffects_top)
        bar_bottom[0].set_path_effects(patheffects_bottom)

        ax.text(
            0.3 if side == "left" else 0.7,
            0.5,
            title,
            ha="center",
            va="center",
            fontsize=10,
            color="black",
            fontproperties=fonts.font_bold.prop,
            rotation=90 if side == "left" else -90,
            rotation_mode="anchor",
            transform=ax.transAxes,
        )
        ax.axis("off")

    @staticmethod
    def process(
        data: pd.DataFrame, axes: Dict[str, Axes], visualisation_parameters: Dict[str, Any]
    ):
        SideBars.possession(axes["possession"], data, visualisation_parameters)
        SideBars.field_tilt(axes["field_tilt"], data, visualisation_parameters)


class VisualiationParameterMaker:

    @staticmethod
    def do_compare(list1, list2, max_score):
        for i in list1:
            for k in list2:

                if VisualiationParameterMaker.color_similarity_score(i, k) < max_score:
                    return i, k

        return None

    @staticmethod
    def create_colors(data, bg_color, conn):
        if not bg_color.startswith("#"):
            bg_color = color_name_to_hex(bg_color)
        default_choices = ["#219ebc", "#023047", "#ffb703", "#fb8500"]
        team_ids = data.groupby("is_home_team")["teamId"].first().to_dict()
        values = list(team_ids.values())
        values_str = str(tuple(values))
        color_data = conn.query(
            "SELECT ws_team_id, color1, color2, color3 FROM mclachbot_teams WHERE ws_team_id IN {}".format(
                values_str
            )
        )
        color_choices = {}
        for ha in [1, 0]:
            if team_ids[ha] not in color_data["ws_team_id"].values:
                color_choices[ha] = default_choices
            else:
                team_colors = color_data[color_data["ws_team_id"] == team_ids[ha]].iloc[0]
                color_choices[ha] = [
                    team_colors["color1"],
                    team_colors["color2"],
                    team_colors["color3"],
                ]

            color_choices[ha] = [
                c
                for c in color_choices[ha]
                if c and VisualiationParameterMaker.color_similarity_score(c, bg_color) < 70
            ]

        choices = VisualiationParameterMaker.do_compare(color_choices[1], color_choices[0], 70)
        if choices is not None:
            return choices

        color_choices[0].extend(default_choices)
        choices = VisualiationParameterMaker.do_compare(color_choices[1], color_choices[0], 70)

        if choices is not None:
            return choices
        color_choices[1].extend(default_choices)
        choices = VisualiationParameterMaker.do_compare(color_choices[1], color_choices[0], 70)

        return choices

    @staticmethod
    def color_similarity_score(hex_color1, hex_color2):
        """
        Calculate a similarity score between two colors in hex format.
        The score ranges from 0 (completely different) to 100 (identical).
        """

        rgb1 = tuple([v * 256 for v in hex_to_rgb(hex_color1)])
        rgb2 = tuple([v * 256 for v in hex_to_rgb(hex_color2)])

        # Calculate the Euclidean distance between the two RGB colors
        distance = sum((rgb1[i] - rgb2[i]) ** 2 for i in range(3)) ** 0.5

        # Normalize the score (0 for max distance, 100 for no distance)
        max_distance = (255**2 + 255**2 + 255**2) ** 0.5
        similarity_score = 100 * (1 - (distance / max_distance))

        return round(similarity_score, 2)

    @staticmethod
    def process(data, conn):
        bg_color = "oldlace"
        colors = VisualiationParameterMaker.create_colors(data, bg_color, conn)

        visualisation_arguments = {
            "facecolor": bg_color,  # Background color
            "away_team_color": colors[1],
            "home_team_color": colors[0],
            "away_color_secondary": "#ffffff",  # White
            "home_color_secondary": "#ffffff",
            "text_color": "black",  # Text color
            "min_dot_size": 50,
            "max_dot_size": 1500,
            "min_line_width": 0.5,
            "max_line_width": 10,
            "min_passes_to_show": 5,
            "max_pass_line_opacity": 0.9,
            "min_pass_line_opacity": 0.1,
            "min_xg_size": np.sqrt(10),
            "max_xg_size": np.sqrt(400),
            "max_xg_value": 0.75,
            "max_size_passes": 75,
            "max_size_touches": 150,
            "pitch_line_color": "grey",
        }
        return visualisation_arguments


class PlayerStats:

    @staticmethod
    def is_progressive(whoscored_df: pd.DataFrame) -> pd.Series:
        """
        Returns a boolean series indicating whether each event in a dataframe is a progressive pass

        Args:
            whoscored_df (pd.DataFrame): The dataframe

        Returns:
            pd.Series: True if the event is a progressive pass, False otherwise

        """

        start_distance_to_goal_middle = distance(
            whoscored_df["x"],
            whoscored_df["y"],
            MIDDLE_GOAL_COORDS[0],
            MIDDLE_GOAL_COORDS[1],
        )
        start_distance_to_goal_top = distance(
            whoscored_df["x"],
            whoscored_df["y"],
            TOP_GOAL_COORDS[0],
            TOP_GOAL_COORDS[1],
        )
        start_distance_to_goal_bottom = distance(
            whoscored_df["x"],
            whoscored_df["y"],
            BOTTOM_GOAL_COORDS[0],
            BOTTOM_GOAL_COORDS[1],
        )
        start_distance = np.minimum(
            start_distance_to_goal_middle,
            np.minimum(start_distance_to_goal_top, start_distance_to_goal_bottom),
        )

        end_distance_to_goal_middle = distance(
            whoscored_df["endX"],
            whoscored_df["endY"],
            MIDDLE_GOAL_COORDS[0],
            MIDDLE_GOAL_COORDS[1],
        )
        end_distance_to_goal_top = distance(
            whoscored_df["endX"],
            whoscored_df["endY"],
            TOP_GOAL_COORDS[0],
            TOP_GOAL_COORDS[1],
        )
        end_distance_to_goal_bottom = distance(
            whoscored_df["endX"],
            whoscored_df["endY"],
            BOTTOM_GOAL_COORDS[0],
            BOTTOM_GOAL_COORDS[1],
        )
        end_distance = np.minimum(
            end_distance_to_goal_middle,
            np.minimum(end_distance_to_goal_top, end_distance_to_goal_bottom),
        )

        is_progressive = (
            (end_distance < start_distance * 0.75)
            & (whoscored_df["event_type"] == EventType.Pass)
            & (~col_has_qualifier(whoscored_df, display_name="CornerTaken"))
        )
        return is_progressive

    @staticmethod
    def progressive_pass_received(data):
        data = data[(data["event_type"] == EventType.Pass) & (data["outcomeType"] == 1)].copy()
        data["prog_pass"] = PlayerStats.is_progressive(data)
        return data.groupby("pass_receiver")["prog_pass"].sum().to_dict()

    @staticmethod
    def change_pos(pos):
        if len(pos) == 4:
            return pos.replace("C", "")
        return pos

    @staticmethod
    def sort_player_names(data):
        non_starters = data[data["event_type"] == EventType.SubstitutionOn]["player_name"].unique()
        sub_offs = data[data["event_type"] == EventType.SubstitutionOff]["player_name"].unique()
        starter_data = data[~data["player_name"].isin(non_starters)]
        starters = extract_names_sorted_by_position(starter_data)
        p_list = []
        for p in starters:
            if p not in sub_offs:
                p_list.append(p)
            else:
                p_list.append(p)
                sub_event = starter_data[
                    (starter_data["player_name"] == p)
                    & (starter_data["event_type"] == EventType.SubstitutionOff)
                ].iloc[0]
                sub_in_event = data[
                    (data["eventId"] == sub_event["relatedEventId"])
                    & (data["teamId"] == sub_event["teamId"])
                ].iloc[0]
                p_list.append(sub_in_event["player_name"])
        return p_list

    @staticmethod
    def mins_played(data):
        max_minute = data["minute"].max()
        players = data["player_name"].unique()
        subs_on = data[data["event_type"] == EventType.SubstitutionOn]
        subs_off = data[data["event_type"] == EventType.SubstitutionOff]
        player_minutes = {}
        for player in players:
            start = 0
            end = max_minute
            if player in subs_on["player_name"].values:
                start = subs_on[subs_on["player_name"] == player]["minute"].values[0]
            if player in subs_off["player_name"].values:
                end = subs_off[subs_off["player_name"] == player]["minute"].values[0]
            player_minutes[player] = end - start
        return player_minutes

    @staticmethod
    def progressive_distance(data):
        data["distance"] = pd_f(data)
        data["distance"] = np.maximum(
            data["distance"]
            * (
                (data["event_type"].isin([EventType.Pass, EventType.Carry])) * (data["outcomeType"])
            ),
            0,
        )
        return data.groupby("player_name")["distance"].sum().to_dict()

    @staticmethod
    def defensive_actions(data):
        data["def_action"] = (
            data["event_type"].isin(
                [
                    EventType.Tackle,
                    EventType.Interception,
                    EventType.BlockedPass,
                    EventType.Clearance,
                    EventType.BallRecovery,
                ]
            )
        ) | ((data["event_type"] == EventType.Foul) & (data["outcomeType"] == 0))
        return data.groupby("player_name")["def_action"].sum().to_dict()

    @staticmethod
    def calc_xa(data):
        data = data.copy()
        data = data[~data["event_type"].isin([EventType.Carry])]
        shots = data[
            data["event_type"].isin(
                [EventType.ShotOnPost, EventType.SavedShot, EventType.MissedShots, EventType.Goal]
            )
        ]
        for _, s in shots.iterrows():

            related_event_id = s["relatedEventId"]
            data.loc[
                (data["eventId"] == related_event_id) & (data["teamId"] == s["teamId"]), "xA"
            ] = s["xG"]
        return data.groupby("player_name")["xA"].sum().to_dict()

    @staticmethod
    def calc_assists(data):
        data = data.copy()
        data = data[~data["event_type"].isin([EventType.Carry])]
        data["assist"] = 0
        assists = data[data["event_type"] == EventType.Goal]
        for _, a in assists.iterrows():
            related_event_id = a["relatedEventId"]
            data.loc[
                (data["eventId"] == related_event_id) & (data["teamId"] == a["teamId"]), "assist"
            ] = 1
        return data.groupby("player_name")["assist"].sum().to_dict()

    @staticmethod
    def player_table(ax, data, team_color):
        locs = {
            "sub_gr": 0.02,
            "pos": 0.05,
            "name": 0.11,
            "minutes": 0.33,
            "goals": 0.38,
            "assists": 0.43,
            "xg": 0.48,
            "xa": 0.55,
            "prog_distance": 0.62,
            "def_actions": 0.69,
            "duels_won": 0.74,
            "prog_pass_rev": 0.79,
            "box_entries": 0.84,
        }
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        # reverse names
        ub_start = 0.98
        names = PlayerStats.sort_player_names(data)
        positions = data.groupby("player_name")["position"].first().to_dict()
        minutes = PlayerStats.mins_played(data)
        for i in range(len(names) + 1):
            ax.axhline(ub_start - i / 17, color="grey", lw=0.5)
        ax.text(
            locs["goals"],
            1,
            "G",
            ha="left",
            va="center",
            fontsize=8,
            color="black",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            locs["assists"],
            1,
            "A",
            ha="left",
            va="center",
            fontsize=8,
            color="black",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            locs["xg"],
            1,
            "xG",
            ha="left",
            va="center",
            fontsize=8,
            color="black",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            locs["xa"],
            1,
            "xA",
            ha="left",
            va="center",
            fontsize=8,
            color="black",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            locs["prog_distance"],
            1,
            "PD",
            ha="left",
            va="center",
            fontsize=8,
            color="black",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            locs["def_actions"],
            1,
            "DA",
            ha="left",
            va="center",
            fontsize=8,
            color="black",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            locs["duels_won"],
            1,
            "DW",
            ha="left",
            va="center",
            fontsize=8,
            color="black",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            locs["prog_pass_rev"],
            1,
            "PR",
            ha="left",
            va="center",
            fontsize=8,
            color="black",
            fontproperties=fonts.font_bold.prop,
        )
        ax.text(
            locs["box_entries"],
            1,
            "BE",
            ha="left",
            va="center",
            fontsize=8,
            color="black",
            fontproperties=fonts.font_bold.prop,
        )

        sub_ons = data[data["event_type"] == EventType.SubstitutionOn]
        sub_offs = data[data["event_type"] == EventType.SubstitutionOff]
        goals = (
            data[
                (data["event_type"] == EventType.Goal)
                & (~col_has_qualifier(data, qualifier_code=28))
            ]
            .groupby("player_name")
            .size()
            .to_dict()
        )
        xgs = data.groupby("player_name")["xG"].sum().to_dict()
        prog_distance = PlayerStats.progressive_distance(data)
        def_actions = PlayerStats.defensive_actions(data)
        xa = PlayerStats.calc_xa(data)
        assists = PlayerStats.calc_assists(data)
        data["duels_won"] = ground_duels_won(data) + aerial_duels_won(data)
        duels_won = data.groupby("player_name")["duels_won"].sum().to_dict()
        pp_received = PlayerStats.progressive_pass_received(data)
        bbox_props = dict(boxstyle="circle,pad=0.1", fc=team_color, ec=team_color, lw=0.5)
        data["box_entry"] = open_play_box_entry(data)
        box_entries = data.groupby("player_name")["box_entry"].sum().to_dict()
        for i, name in enumerate(names):
            if name in sub_ons["player_name"].values:
                ax.scatter(
                    locs["sub_gr"],
                    ub_start - (i + 0.5) / 17,
                    s=10,
                    color="green",
                    edgecolor="green",
                    zorder=3,
                    marker="^",
                )
            if name in sub_offs["player_name"].values:
                ax.scatter(
                    locs["sub_gr"],
                    ub_start - (i + 0.5) / 17,
                    s=10,
                    color="red",
                    edgecolor="red",
                    zorder=3,
                    marker="v",
                )
            ax.text(
                locs["pos"],
                ub_start - (i + 0.5) / 17,
                PlayerStats.change_pos(positions[name]),
                ha="left",
                va="center",
                fontsize=8,
                color="grey",
                fontproperties=fonts.font_bold.prop,
            )
            ax.text(
                locs["name"],
                ub_start - (i + 0.5) / 17,
                smartest_name_formatter_yet(name, 15),
                ha="left",
                va="center",
                fontsize=8,
                color="black",
                fontproperties=fonts.font_bold.prop,
            )
            ax.text(
                locs["minutes"],
                ub_start - (i + 0.5) / 17,
                f"{minutes[name]}'",
                ha="left",
                va="center",
                fontsize=8,
                color="grey",
                fontproperties=fonts.font_bold.prop,
            )

            g = goals.get(name, 0)

            if g > 0:
                if g == max(goals.values()):
                    # _draw_semirounded_box(ax, locs['goals'], ub_start-(i+0.5)/17, 0.01, 0.02, facecolor=team_color, edgecolor=team_color)
                    ax.text(
                        locs["goals"],
                        ub_start - (i + 0.5) / 17,
                        g,
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="oldlace",
                        fontproperties=fonts.font_bold.prop,
                        bbox=bbox_props,
                    )

                else:
                    ax.text(
                        locs["goals"],
                        ub_start - (i + 0.5) / 17,
                        g,
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="black",
                        fontproperties=fonts.font_bold.prop,
                    )
            xg = xgs.get(name, 0)
            if xg > 0:
                if xg == max(xgs.values()):

                    ax.text(
                        locs["xg"],
                        ub_start - (i + 0.5) / 17,
                        f"{xg:.2f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="oldlace",
                        fontproperties=fonts.font_bold.prop,
                        bbox=bbox_props,
                    )
                else:
                    ax.text(
                        locs["xg"],
                        ub_start - (i + 0.5) / 17,
                        f"{xg:.2f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="black",
                        fontproperties=fonts.font_bold.prop,
                    )
            pd = prog_distance.get(name, 0)
            if pd > 0:
                if pd == max(prog_distance.values()):
                    ax.text(
                        locs["prog_distance"],
                        ub_start - (i + 0.5) / 17,
                        f"{pd:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="oldlace",
                        fontproperties=fonts.font_bold.prop,
                        bbox=bbox_props,
                    )
                else:
                    ax.text(
                        locs["prog_distance"],
                        ub_start - (i + 0.5) / 17,
                        f"{pd:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="black",
                        fontproperties=fonts.font_bold.prop,
                    )

            da = def_actions.get(name, 0)
            if da > 0:
                if da == max(def_actions.values()):
                    ax.text(
                        locs["def_actions"],
                        ub_start - (i + 0.5) / 17,
                        f"{da:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="oldlace",
                        fontproperties=fonts.font_bold.prop,
                        bbox=bbox_props,
                    )
                else:
                    ax.text(
                        locs["def_actions"],
                        ub_start - (i + 0.5) / 17,
                        f"{da:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="black",
                        fontproperties=fonts.font_bold.prop,
                    )

            x_a = xa.get(name, 0)
            if x_a > 0:
                if x_a == max(xa.values()):
                    ax.text(
                        locs["xa"],
                        ub_start - (i + 0.5) / 17,
                        f"{x_a:.2f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="oldlace",
                        fontproperties=fonts.font_bold.prop,
                        bbox=bbox_props,
                    )
                else:
                    ax.text(
                        locs["xa"],
                        ub_start - (i + 0.5) / 17,
                        f"{x_a:.2f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="black",
                        fontproperties=fonts.font_bold.prop,
                    )
            a = assists.get(name, 0)
            if a > 0:
                if a == max(assists.values()):
                    ax.text(
                        locs["assists"],
                        ub_start - (i + 0.5) / 17,
                        f"{a:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="oldlace",
                        fontproperties=fonts.font_bold.prop,
                        bbox=bbox_props,
                    )
                else:
                    ax.text(
                        locs["assists"],
                        ub_start - (i + 0.5) / 17,
                        f"{a:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="black",
                        fontproperties=fonts.font_bold.prop,
                    )

            dw = duels_won.get(name, 0)
            if dw > 0:
                if dw == max(duels_won.values()):
                    ax.text(
                        locs["duels_won"],
                        ub_start - (i + 0.5) / 17,
                        f"{dw:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="oldlace",
                        fontproperties=fonts.font_bold.prop,
                        bbox=bbox_props,
                    )
                else:
                    ax.text(
                        locs["duels_won"],
                        ub_start - (i + 0.5) / 17,
                        f"{dw:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="black",
                        fontproperties=fonts.font_bold.prop,
                    )

            ppr = pp_received.get(name, 0)
            if ppr > 0:
                if ppr == max(pp_received.values()):
                    ax.text(
                        locs["prog_pass_rev"],
                        ub_start - (i + 0.5) / 17,
                        f"{ppr:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="oldlace",
                        fontproperties=fonts.font_bold.prop,
                        bbox=bbox_props,
                    )
                else:
                    ax.text(
                        locs["prog_pass_rev"],
                        ub_start - (i + 0.5) / 17,
                        f"{ppr:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="black",
                        fontproperties=fonts.font_bold.prop,
                    )

            be = box_entries.get(name, 0)
            if be > 0:
                if be == max(box_entries.values()):
                    ax.text(
                        locs["box_entries"],
                        ub_start - (i + 0.5) / 17,
                        f"{be:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="oldlace",
                        fontproperties=fonts.font_bold.prop,
                        bbox=bbox_props,
                    )
                else:
                    ax.text(
                        locs["box_entries"],
                        ub_start - (i + 0.5) / 17,
                        f"{be:.0f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="black",
                        fontproperties=fonts.font_bold.prop,
                    )

    def process(data, axes, visualisation_parameters):
        home_data = data[data["is_home_team"] == 1]

        PlayerStats.player_table(
            axes["left_stats"], home_data, visualisation_parameters["home_team_color"]
        )
        away_data = data[data["is_home_team"] == 0]
        PlayerStats.player_table(
            axes["right_stats"], away_data, visualisation_parameters["away_team_color"]
        )


class Footer:
    @staticmethod
    def footer(ax):
        ax.axis("off")
        legend_text = "<Stat Legend:>\n<G> - Goals  <A> - Assists   <xG> - Expected Goals   <xA> - Expected Assists   <PD> - Progressive Distance\n<DA> - Defensive Actions   <DW> - Duels Won   <PR> - Progressive Passes Received   <BE> - Box Entries"
        ht.ax_text(
            0.01,
            0.5,
            legend_text,
            ha="left",
            va="center",
            fontsize=8,
            color="grey",
            fontproperties=fonts.font_bold.prop,
            ax=ax,
            highlight_textprops=[
                {"color": "black"},
                {"color": "black"},
                {"color": "black"},
                {"color": "black"},
                {"color": "black"},
                {"color": "black"},
                {"color": "black"},
                {"color": "black"},
                {"color": "black"},
                {"color": "black"},
            ],
        )
        aspect = get_aspect(ax)
        mclachbot_axis = ax.inset_axes([1 - aspect, 0, aspect, 1])
        mclachbot_axis.axis("off")
        mclachbot_axis.imshow(get_ball_logo2())
        ax.text(
            0.5,
            0.5,
            "Design is based heavily on John Muller's match dashboard design for The Athletic",
            ha="center",
            va="center",
            fontsize=8,
            color="grey",
            fontproperties=fonts.font_bold.prop,
        )


class PassNetworks:

    @staticmethod
    def initial_data_clean(data: pd.DataFrame, is_home_team: bool) -> pd.DataFrame:
        """
        This function filters the data to the initial formation of the team. It also shortens
        some of the position names.
        """
        VALID_EVENTS = [
            EventType.Pass,
            EventType.Aerial,
            EventType.BallRecovery,
            EventType.BallTouch,
            EventType.Challenge,
            EventType.ShotOnPost,
            EventType.SavedShot,
            EventType.MissedShots,
            EventType.Goal,
            EventType.TakeOn,
            EventType.Foul,
            EventType.Interception,
            EventType.Tackle,
            EventType.GoodSkill,
            EventType.Challenge,
            EventType.Clearance,
        ]

        data = data[data["is_home_team"] == is_home_team]
        data["is_successful"] = data["outcomeType"] == 1
        data = data[data["event_type"].isin(VALID_EVENTS)]
        data = data[
            data["formation"] == data[data["formation"].notnull()]["formation"].iloc[0]
        ].copy()

        data["position"] = data["position"].apply(
            lambda x: x.replace("C", "") if isinstance(x, str) and len(x) == 4 else x
        )
        data["pass_receiver_position"] = data["pass_receiver_position"].apply(
            lambda x: x.replace("C", "") if isinstance(x, str) and len(x) == 4 else x
        )
        return data

    @staticmethod
    def aggregate_touches(data: pd.DataFrame) -> pd.DataFrame:
        """
        This function aggregates the touches of each player
        """
        data = (
            data.groupby(["position"])
            .agg({"x": "mean", "y": "mean", "player_name": "count"})
            .reset_index()
            .rename(columns={"player_name": "touches"})
        )
        return data

    @staticmethod
    def aggregate_pass_pairs(data: pd.DataFrame) -> pd.DataFrame:
        """
        This function aggregates the pass pairs.  We will also filter out
        any incomplete passes. Finally we need to combine the pairs so that x->y and y->x are combined
        """
        data = data[data["event_type"] == EventType.Pass]
        data = data[data["is_successful"] == 1]

        data = (
            data.groupby(["position", "pass_receiver_position"])
            .agg({"x": "count"})
            .reset_index()
            .rename(columns={"x": "passes"})
        )
        data["player_1_position"] = data.apply(
            lambda x: min(x["position"], x["pass_receiver_position"]), axis=1
        )
        data["player_2_position"] = data.apply(
            lambda x: max(x["position"], x["pass_receiver_position"]), axis=1
        )
        data = (
            data.groupby(["player_1_position", "player_2_position"])
            .agg({"passes": "sum"})
            .reset_index()
        )
        return data

    @staticmethod
    def plot_average_positions(
        data: pd.DataFrame, pitch: VerticalPitch, ax: Axes, visualisation_parameters: dict
    ) -> None:
        """
        This function plots the average positions of the players
        """

        x = data["x"]
        y = data["y"]
        s = [
            visualisation_parameters["min_dot_size"]
            + (t / visualisation_parameters["max_size_touches"])
            * (visualisation_parameters["max_dot_size"] - visualisation_parameters["min_dot_size"])
            for t in data["touches"]
        ]
        pitch.scatter(x, y, s=s, color=visualisation_parameters["chart_color"], ax=ax, zorder=3)
        for _, row in data.iterrows():
            x = row["x"]
            y = row["y"]
            position = row["position"]
            pitch.annotate(
                position,
                (x, y),
                ax=ax,
                fontsize=8,
                color=visualisation_parameters["text_color"],
                ha="center",
                va="center",
                zorder=4,
            )

    @staticmethod
    def plot_passing_lines(
        pass_data: pd.DataFrame,
        player_location_data: pd.DataFrame,
        pitch: VerticalPitch,
        ax: Axes,
        visualisation_parameters: dict,
    ) -> None:

        for _, row in pass_data.iterrows():
            if row["passes"] < visualisation_parameters["min_passes_to_show"]:
                continue

            player_1 = row["player_1_position"]
            player_2 = row["player_2_position"]
            passes = row["passes"]
            player_1_x = player_location_data[player_location_data["position"] == player_1][
                "x"
            ].values[0]
            player_1_y = player_location_data[player_location_data["position"] == player_1][
                "y"
            ].values[0]
            player_2_x = player_location_data[player_location_data["position"] == player_2][
                "x"
            ].values[0]
            player_2_y = player_location_data[player_location_data["position"] == player_2][
                "y"
            ].values[0]
            line_width = visualisation_parameters["min_line_width"] + (
                passes / visualisation_parameters["max_size_passes"]
            ) * (
                visualisation_parameters["max_line_width"]
                - visualisation_parameters["min_line_width"]
            )
            line_opacity = visualisation_parameters["min_pass_line_opacity"] + (
                passes / visualisation_parameters["max_size_passes"]
            ) * (
                visualisation_parameters["max_pass_line_opacity"]
                - visualisation_parameters["min_pass_line_opacity"]
            )
            pitch.lines(
                player_1_x,
                player_1_y,
                player_2_x,
                player_2_y,
                lw=line_width,
                color=visualisation_parameters["pass_line_color"],
                ax=ax,
                zorder=2,
                alpha=line_opacity,
            )

    @staticmethod
    def plot_pass_network(data, is_home, pitch, ax, visualisation_parameters):
        vis_parameters = visualisation_parameters.copy()
        if is_home:
            vis_parameters["chart_color"] = visualisation_parameters["home_team_color"]
            vis_parameters["text_color"] = visualisation_parameters["home_color_secondary"]
            vis_parameters["pass_line_color"] = visualisation_parameters["home_team_color"]
        else:
            vis_parameters["chart_color"] = visualisation_parameters["away_team_color"]
            vis_parameters["text_color"] = visualisation_parameters["away_color_secondary"]
            vis_parameters["pass_line_color"] = visualisation_parameters["away_team_color"]
        data = PassNetworks.initial_data_clean(data, is_home)
        touch_data = PassNetworks.aggregate_touches(data)
        pass_data = PassNetworks.aggregate_pass_pairs(data)
        PassNetworks.plot_average_positions(touch_data, pitch, ax, vis_parameters)
        PassNetworks.plot_passing_lines(pass_data, touch_data, pitch, ax, vis_parameters)
        max_minutes = data["minute"].max()
        pitch.text(
            -0.5,
            0.1,
            f"Data from first {max_minutes} minutes",
            ha="right",
            va="top",
            fontsize=8,
            color="grey",
            ax=ax,
        )
        small_pitch_ax = pitch.inset_axes(95, 5, 9, 9, ax=ax, zorder=300)
        formation = data["formation"].iloc[0]
        small_pitch = VerticalPitch(
            "opta",
            pitch_color=visualisation_parameters["facecolor"],
            line_color=visualisation_parameters["pitch_line_color"],
            linewidth=1,
            line_alpha=0.5,
        )
        small_pitch.draw(small_pitch_ax)
        positionslist = small_pitch.get_formation(formation)

        for position in positionslist:
            x, y = position.x, position.y
            small_pitch.scatter(x, y, color=vis_parameters["chart_color"], s=15, ax=small_pitch_ax)

    @staticmethod
    def process(data, axes, visualisation_parameters):
        pitch_left = VerticalPitch(
            pitch_type="opta",
            pitch_color=visualisation_parameters["facecolor"],
            line_color=visualisation_parameters["pitch_line_color"],
            line_zorder=1,
            linewidth=1,
        )
        pitch_left.draw(axes["left_pn"])
        pitch_right = VerticalPitch(
            pitch_type="opta",
            pitch_color=visualisation_parameters["facecolor"],
            line_color=visualisation_parameters["pitch_line_color"],
            line_zorder=1,
            linewidth=1,
        )
        pitch_right.draw(axes["right_pn"])
        PassNetworks.plot_pass_network(
            data, True, pitch_left, axes["left_pn"], visualisation_parameters
        )
        PassNetworks.plot_pass_network(
            data, False, pitch_right, axes["right_pn"], visualisation_parameters
        )


def create_dashboard(conn, match_id):
    data = get_dataframe_for_match(match_id, conn)

    data["event_type"] = data["event_type"].apply(lambda x: EventType(x.value))
    league = data["competition"].values[0]
    match_data = generate_match_stats(data)
    context_data = get_match_stat_history(league, conn)
    visualisation_parameters = VisualiationParameterMaker.process(data, conn)
    fig, axes = create_layout(visualisation_parameters["facecolor"])
    MatchStats.match_stats_ax(
        axes["match_stats"], match_data, context_data, visualisation_parameters
    )
    GameFlow.process(data, axes["gameflow"], visualisation_parameters)
    PassNetworks.process(data, axes, visualisation_parameters)
    Heatmap.process(axes["heatmap"], data, visualisation_parameters)
    ShotMap.process(data, axes["shot_map"], visualisation_parameters)
    Header.create_header(axes["header"], data, visualisation_parameters)
    SideBars.process(data, axes, visualisation_parameters)
    PlayerStats.process(data, axes, visualisation_parameters)
    Footer.footer(axes["bottom"])
    return fig, axes
