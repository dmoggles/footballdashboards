import pandas as pd
import numpy as np
from footballdashboards.dashboard.dashboard import Dashboard
from footballdashboards._types._custom_types import PlotReturnType
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Tuple, Dict
from mplsoccer import VerticalPitch, set_visible, Pitch
from footballdashboards.helpers.mplsoccer_helpers import make_grid, get_ax_size
from footballdashboards._types._dashboard_fields import DashboardField, ColorField
from footballdashboards.helpers.fonts import font_bold, font_italic, font_normal
from footballdashboards.helpers.mclachbot_helpers import McLachBotBadgeService
from PIL.PngImagePlugin import PngImageFile
from highlight_text import ax_text
from footballdashboards.helpers.mclachbot_helpers import get_ball_logo

class BestElevenDashboard(Dashboard):

    figheight = DashboardField(description="Figure height", default=14)
    linecolor = ColorField(description="Pitch line colour", default="#000000")
    textcolor = ColorField(description="Text colour", default="#000000")
    title = DashboardField(description="Title", default="Best Eleven")

    def __init__(self, data_accessor):
        super().__init__(data_accessor)

    @property
    def datasource_name(self):
        return "besteleven"

    def _required_data_columns(self):
        return {
            "player": "Player name",
            "season": "Season",
            "league": "League",
            "position": "Position",
            "squad": "Team name",

        }
    
    def _setup_pitch(self)->Tuple[Figure, Axes]:
        pitch = VerticalPitch(pitch_type="opta", line_zorder=4, pitch_color=self.facecolor, line_color=self.linecolor, linewidth=1, line_alpha=0.1)
        fig, axes = make_grid(
            pitch=pitch,
            figheight=self.figheight,
            title_height=0.05,
            title_space=0,
            endnote_height=0.05,
            endnote_space=0,
        )
        fig.set_facecolor(self.facecolor)
        for ax_name in ["title", "endnote"]:
            axes[ax_name].axis("off")
        return fig, axes, pitch
    
    def _draw_title_ax(self, pitch:Pitch, ax:Axes, data:pd.DataFrame):
        ax.set_facecolor(self.facecolor)
        ax.text(
            0.05,
            0.7,
            self.title,
            ha="left",
            va="center",
            fontsize=24,
            color=self.textcolor,
            fontproperties=font_bold.prop,
        )
        data['tag'] = data['tag'].fillna('')
        if "tag" in data.columns and data["tag"].iloc[0]!='':
            title_second_part = data['tag'].iloc[0]
        else:
            title_second_part = f'{data["season"].iloc[0]}'
        ax.text(
            0.05,
            0.2,
            f'{data["league_name"].iloc[0]} {title_second_part}',
            ha="left",
            va="center",
            fontsize=16,
            color=self.textcolor,
            fontproperties=font_bold.prop,
        )

        league_image = McLachBotBadgeService().league_badge(data["league"].iloc[0])

        ax_width, ax_height = get_ax_size(ax, ax.get_figure())

        target_height = 1.1
        target_width = target_height * ax_height / ax_width

        ax_img = pitch.inset_axes(
            y=1 - target_width / 2.0,
            x=0.5,
            width=target_width,
            length=target_height,
            ax=ax,
        )
        ax_img.set_facecolor(self.facecolor)
        set_visible(ax_img)
        ax_img.imshow(league_image)
    
    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes, pitch = self._setup_pitch()
        self._draw_title_ax(pitch=pitch, ax=axes["title"], data=data)
        team_badges = self._get_team_badge_table(data)
        self._draw_endnote(pitch=pitch, ax=axes["endnote"])
        self._draw_pitch(data=data, pitch=pitch, ax=axes["pitch"], team_badges=team_badges)
        return fig, axes
    

    def _get_team_badge_table(self, data):
        team_name_table = data[["league",'squad']].drop_duplicates()
        league = data["league"].iloc[0]
        team_badges = {
            team_name: McLachBotBadgeService().team_badge( league, team_name)
            for team_name in team_name_table["squad"]
        }
        return team_badges
    
    def _draw_endnote(self, pitch:Pitch, ax:Axes):
        ax.set_facecolor(self.facecolor)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.scatter(
            0.02,
            0.5,
            color="gold",
            marker="*",
            s=200,
            linewidth=1,
            edgecolor="black",
            zorder=5,
        )
        ax.text(
            0.045,
            0.5,
            "Best Player",
            color=self.textcolor,
            fontsize=10,
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
        )
        diamond_inset = pitch.inset_axes(0.5, 0.35, length=0.8, aspect=1, ax=ax)
        self._draw_diamond(diamond_inset, 0.6, 0.6, 0.6, 0.6)
        ax.text(
            0.305,
            0.5,
            "progressing",
            color=self.textcolor,
            alpha=0.5,
            fontsize=9,
            ha="right",
            va="center",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.35,
            1.1,
            "shooting",
            color=self.textcolor,
            alpha=0.5,
            fontsize=9,
            ha="center",
            va="top",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.35,
            -0.1,
            "defending",
            color=self.textcolor,
            alpha=0.5,
            fontsize=9,
            ha="center",
            va="bottom",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.395,
            0.5,
            "creating",
            color=self.textcolor,
            alpha=0.5,
            fontsize=9,
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
        )

        triange_inset = pitch.inset_axes(0.5, 0.65, length=0.8, aspect=1, ax=ax)
        self._draw_equalateral_triangle(triange_inset, 0.6, 0.6, 0.6)
        ax.text(
            0.65,
            1.1,
            "shot stopping",
            color=self.textcolor,
            alpha=0.5,
            fontsize=9,
            ha="center",
            va="top",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.6,
            0.2,
            "distribution",
            color=self.textcolor,
            alpha=0.5,
            fontsize=9,
            ha="right",
            va="center",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.7,
            0.2,
            "area control",
            color=self.textcolor,
            alpha=0.5,
            fontsize=9,
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
        )

        logo_ax = pitch.inset_axes(0.5, 0.90, length=0.8, aspect=1, ax=ax)
        logo_ax.axis("off")
        logo_ax.imshow(get_ball_logo())
        ax.text(
            0.90,
            1.1,
            "Created by @McLachBot",
            color=self.textcolor,
            alpha=0.5,
            fontsize=8,
            ha="center",
            va="top",
            fontproperties=font_italic.prop,
        )
        ax.text(
            0.90,
            -0.1,
            "Data from FBref.com",
            color=self.textcolor,
            alpha=0.5,
            fontsize=8,
            ha="center",
            va="bottom",
            fontproperties=font_italic.prop,
        )

    def _draw_diamond(self, ax, left, bottom, right, top):
        ax.set_facecolor(self.facecolor)
        ax.set_alpha(0.0)
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        set_visible(ax)
        for i in range(1, 4):
            ax.plot(
                [0, i / 3.0, 0, -i / 3.0, 0],
                [i / 3.0, 0, -i / 3.0, 0, i / 3.0],
                color=self.linecolor,
                linewidth=1,
                alpha=0.2,
            )
        ax.fill(
            [-left, 0, right, 0],
            [0, top, 0, -bottom],
            color="red",
            linewidth=1,
            alpha=0.2,
        )
        ax.scatter(0, 0, color=self.linecolor, s=3)

    def _draw_equalateral_triangle(self, ax, top, left, right):
        ax.set_facecolor(self.facecolor)
        ax.set_alpha(0.0)
        ax.set_xlim(-np.sqrt(3) / 2, np.sqrt(3) / 2)
        ax.set_ylim(-0.5, 1)
        set_visible(ax)
        for i in range(3, 0, -1):
            ax.plot(
                [
                    -(i / 3) * np.sqrt(3) / 2,
                    0,
                    (i / 3) * np.sqrt(3) / 2,
                    -(i / 3) * np.sqrt(3) / 2,
                ],
                [
                    -(i / 3) * 0.5,
                    (i / 3) * 1,
                    -(i / 3) * 0.5,
                    -(i / 3) * 0.5,
                ],
                color=self.linecolor,
                linewidth=1,
                alpha=0.2,
            )

        ax.fill(
            [
                -(left) * np.sqrt(3) / 2,
                0,
                (right) * np.sqrt(3) / 2,
                -(left) * np.sqrt(3) / 2,
            ],
            [
                -(left) * 0.5,
                (top) * 1,
                -(right) * 0.5,
                -(left) * 0.5,
            ],
            color="magenta",
            linewidth=1,
            alpha=0.2,
        )
        ax.scatter(0, 0, color=self.linecolor, s=3)

    def _draw_pitch(
        self, data, pitch: VerticalPitch, ax: Axes, team_badges: Dict[str, PngImageFile]
    ):
        formation = data['formation'].iloc[0]
        positions_axes = pitch.inset_formation_axes(formation, length=12, aspect=1, ax=ax)
        for position, ax_inner in positions_axes.items():
            self._draw_one_position(data, pitch, ax_inner, position, team_badges)
        ax_text(
            0.99,
            0.01,
            "All stats except <Goals>, <Assists> and\n<Clean Sheets> are per 90 minutes",
            color=self.textcolor,
            fontsize=8,
            ha="right",
            va="bottom",
            fontproperties=font_italic.prop,
            highlight_textprops=[{"color": "red"} for _ in range(3)],
            ax=ax,

        )
        

    def _draw_one_position(
        self,
        data,
        pitch: VerticalPitch,
        ax: Axes,
        position: str,
        team_badges: Dict[str, PngImageFile],
    ):
        set_visible(ax)
        ax.set_facecolor(self.facecolor)
        ax.set_alpha(0.0)
        data_position = data[data["placement_position"] == position]

        badge_image_inset = pitch.inset_axes(
            x=0.75, y=0.25, width=0.5, length=0.5, ax=ax
        )
        set_visible(badge_image_inset)
        badge_image_inset.imshow(team_badges[data_position["squad"].iloc[0]], zorder=5)
        badge_image_inset.set_facecolor(self.facecolor)
        performance_inset = pitch.inset_axes(
            x=0.75, y=0.75, width=0.5, length=0.5, ax=ax
        )

        if position == "GK":
            self._draw_equalateral_triangle(
                performance_inset,
                data_position["shotstopping_ranking"].iloc[0],
                data_position["distribution_ranking"].iloc[0],
                data_position["area_control_ranking"].iloc[0],
            )
        else:
            self._draw_diamond(
                performance_inset,
                data_position["progressing_ranking"].iloc[0],
                data_position["defending_ranking"].iloc[0],
                data_position["providing_ranking"].iloc[0],
                data_position["finishing_ranking"].iloc[0],
            )

        if data_position["total"].iloc[0] == data["total"].max():
            badge_image_inset.scatter(
                80,
                80,
                color="gold",
                alpha=1,
                marker="*",
                zorder=10,
                s=200,
                linewidth=1,
                edgecolor="black",
            )
        player_name = self._player_name_format(data_position["player"].iloc[0])
        ax.text(
            0.0,
            0.4,
            player_name,
            ha="left",
            va="center",
            fontsize=10,
            color=self.textcolor,
            fontproperties=font_normal.prop,
        )

       

        texts = "\n".join(
            [
                self._get_stat_text(
                    data_position[f"top_category_{i}"].iloc[0],
                    data_position[f"top_value_{i}"].iloc[0],
                )
                for i in range(1, 4)
            ]
        )
        ax.text(
            0.0,
            0.3,
            texts,
            ha="left",
            va="top",
            fontsize=8,
            color=self.textcolor,
            fontproperties=font_normal.prop,
        )
       
    def _get_stat_text(self, category, value):
        display_category = category.replace("_", " ").title()
        replacements = {
            "Passes Into Penalty Area": "Passes Into Box",
            "Passes Progressive Distance":"Prog Pass Dist",
            "Passes Into Final Third": "Passes Into Att 1/3",
            "Progressive Passes": "Prog Passes",
            "Sca": "Created Shots",
            "Psxg": "PSxG Overperformance",
            "Crosses Stopped Gk": "Crosses Claimed",
            " P90":"",
        }
        no_number_categories = [
            "clean_sheets",
            "winning_goals",
            "equalising_goals",
            "opening_goals",
        ]
        #display_category = replacements.get(display_category, display_category)
        for k, v in replacements.items():
            display_category = display_category.replace(k, v)

        if value == 1 and display_category.endswith("s"):
            display_category = display_category[:-1]

        if category in no_number_categories and value == 1:
            return display_category
        if category == "pass_completed_pct":
            value += 0.75
        
        if value.is_integer():
            value = int(value)
            value = f"{value:.0f}"
        elif value < 2:
            value = round(value, 2)
            value = f"{value:.2f}"
        elif value < 10:
            value = round(value, 1)
            value = f"{value:.1f}"
        else:
            value = round(value, 0)
            value = f"{value:.0f}"
        return (
            f"{value} {display_category}"
            
        )
    def _player_name_format(self, player_name):
        tokens = player_name.split(" ")
        if len(tokens) > 2:
            abbreviations = " ".join([f"{t[0].upper()}." for t in tokens[1:-1]])

            return f"{tokens[0].title()} {abbreviations} {tokens[2].title()}"
        else:
            return player_name.title()
