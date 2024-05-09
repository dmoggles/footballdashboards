from matplotlib.figure import Figure
from matplotlib.axes import Axes
import pandas as pd
import numpy as np
from footballdashboards._types._dashboard_fields import (
    ColorField,
    FigSizeField,
    DashboardField,
    is_color_like,
)
from footballdashboards.helpers.utils import is_high_luminance
from footballdashboards._types._custom_types import PlotReturnType
from footballdashboards.helpers.mclachbot_helpers import (
    McLachBotBadgeService,
    CachedPlayerImageHelper,
)
from footballdashboards.helpers.matplotlib import get_aspect
from footballdashboards.helpers.formatters import smartest_name_formatter_yet
from footballdashboards.helpers.fonts import font_europa, font_normal, font_italic
from scipy.ndimage import rotate
from PIL import Image
from urllib.request import urlopen
from footballdashboards.dashboard.radardashboard import RadarDashboard


class NewStyleRadarDashboard(RadarDashboard):
    PLAYER_IMAGE_CACHE_URL = None
    PRESERVE_FULLSIZE_CUTOUT = False
    SCOUTED_IMAGE_LOCATION = None
    FIG_SIZE_DEFAULT = (4 * 1.5, 6 * 1.5)
    fig_size = FigSizeField(description="Figure size", default=FIG_SIZE_DEFAULT)

    def _template_color(self, template_name: str = None):
        templates = {
            "Midfielder": "blue",
            "Centre Back": "green",
            "Full Back": "orange",
            "Forward": "red",
            "Attacking Midfielder/Winger": "pink",
            "Combined Fwd/AM": "grey",
            "Goalkeeper": "purple",
            "Targetman Forward": "black",
        }
        return templates[template_name]

    def _setup_figure(self):
        fig = Figure(figsize=(6.75, 9), dpi=100, facecolor=self.facecolor)
        axes = {}
        axes["radar"] = fig.add_axes((0, 0.01, 1, 0.81), facecolor=self.facecolor, aspect="equal")
        axes["title"] = fig.add_axes((0, 0.82, 1.0, 0.18), facecolor=self.facecolor)
        axes["title"].axis("off")
        axes["endnote"] = fig.add_axes((0, 0, 1, 0.01), facecolor=self.facecolor)
        axes["endnote"].axis("off")

        return fig, axes

    def _place_team_logo(self, team: str, league, ax: Axes, fig: Figure, side: str):
        img = McLachBotBadgeService().team_badge(league, team)
        img = np.array(list(img.convert("RGBA").getdata())).reshape(img.height, img.width, 4)
        rotate_angle = 10 if side == "left" else -10
        rotated_img = rotate(img, rotate_angle, reshape=True)
        if side == "left":
            rotated_img = rotated_img[
                int(rotated_img.shape[0] / 5) : rotated_img.shape[0],
                int(rotated_img.shape[1] / 5) : rotated_img.shape[1],
            ]
        else:
            rotated_img = rotated_img[
                int(rotated_img.shape[0] / 5) : rotated_img.shape[0],
                0 : int(rotated_img.shape[1] - rotated_img.shape[1] / 5),
            ]
        fig_aspect = fig.get_figheight() / fig.get_figwidth()
        img_size = 0.15
        if side == "left":
            ax = fig.add_axes([0, 1 - img_size, img_size * fig_aspect, img_size], zorder=0.1)
        else:
            ax = fig.add_axes(
                [1 - img_size * fig_aspect, 1 - img_size, img_size * fig_aspect, img_size],
                zorder=0.1,
            )
        ax.axis("off")
        ax.imshow(rotated_img, alpha=0.2)

    def _draw_line(self, ax: Axes):
        ax.fill([0.04, 0.51, 0.49, 0.04], [0.04, 0.04, 0.0, 0.0], c=self.radar_colors[0])
        ax.fill([0.49, 0.96, 0.96, 0.51], [0.0, 0.0, 0.04, 0.04], c=self.radar_colors[1])

    def _draw_name(self, player_name1: str, player_name2: str, ax: Axes):
        ax.text(
            0.06,
            0.9,
            smartest_name_formatter_yet(player_name1),
            fontproperties=font_europa.prop,
            fontsize=24,
            ha="left",
            va="top",
            zorder=10,
        )
        ax.text(
            0.94,
            0.1,
            smartest_name_formatter_yet(player_name2),
            fontproperties=font_europa.prop,
            fontsize=24,
            ha="right",
            va="bottom",
            zorder=10,
        )

    def _format_season(self, season, league_name):
        if league_name in ["MLS", "Brasilian Serie A", "NWSL", "Argentine Primera", "World Cup"]:
            return f"{season} season"
        else:
            return f"{season}/{str(season+1)[-2:]} season"

    def _draw_subheader(
        self,
        minutes: str,
        team_name: str,
        league_name: str,
        season: str,
        age: str,
        date_label: str,
        ax: Axes,
        side: str,
    ):
        tokens = league_name.split(",")
        if len(tokens) > 1:
            # strip champions league and europa league
            league_name = (
                next(t for t in tokens if "Champions League" not in t and "Europa League" not in t)
                + "*"
            )
        season_str = self._format_season(season, league_name)
        full_str1 = f"{minutes:.0f} minutes | {age:.0f} years old"
        full_str2 = f"{team_name} | {league_name.replace(',',', ')} | {season_str}"
        if side == "left":
            ax.text(
                0.05,
                0.72,
                full_str1,
                fontproperties=font_normal.prop,
                fontsize=10,
                ha="left",
                va="top",
                zorder=10,
            )
            ax.text(
                0.05,
                0.62,
                full_str2,
                fontproperties=font_normal.prop,
                fontsize=10,
                ha="left",
                va="top",
                zorder=10,
            )
            ax.text(
                0.05,
                -0.08,
                date_label,
                fontproperties=font_italic.prop,
                fontsize=9,
                ha="left",
                va="top",
                zorder=10,
            )

        else:
            ax.text(
                0.95,
                0.28,
                full_str1,
                fontproperties=font_normal.prop,
                fontsize=10,
                ha="right",
                va="bottom",
                zorder=10,
            )
            ax.text(
                0.95,
                0.38,
                full_str2,
                fontproperties=font_normal.prop,
                fontsize=10,
                ha="right",
                va="bottom",
                zorder=10,
            )
            ax.text(
                0.95,
                -0.08,
                date_label,
                fontproperties=font_italic.prop,
                fontsize=9,
                ha="right",
                va="top",
                zorder=10,
            )

    def _plot_cutout(self, player_id: str, ax: Axes, side: str):
        aspect = get_aspect(ax)
        if side == "left":
            height = 0.4
            insert_ax = ax.inset_axes([0.25 - height * aspect / 2, 0.05, height * aspect, height])
        else:
            height = 0.4
            insert_ax = ax.inset_axes([0.75 - height * aspect / 2, 0.55, height * aspect, height])
        insert_ax.axis("off")
        img = CachedPlayerImageHelper(self.PLAYER_IMAGE_CACHE_URL).get_player_image(player_id)
        if img is None:
            return
        img = np.array(list(img.convert("RGBA").getdata())).reshape(img.height, img.width, 4)

        img = np.array(img)
        if not self.PRESERVE_FULLSIZE_CUTOUT:
            img = img[
                int(img.shape[0] * 0.0) : int(img.shape[0] * 0.5),
                int(img.shape[1] * 0.25) : int(img.shape[1] * 0.75),
            ]
        insert_ax.imshow(img, alpha=1)

    def _plot_header(self, ax: Axes, data: pd.DataFrame, fig: Figure):
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
        date_label_1 = data["DateLabel"].iloc[0]
        date_lable_2 = data["DateLabel"].iloc[1]
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        self._place_team_logo(image_name_1, image_league_1, ax, fig, side="left")
        self._place_team_logo(image_name_2, image_league_2, ax, fig, side="right")
        self._draw_line(ax)
        self._draw_name(player_1_name, player_2_name, ax)
        self._draw_subheader(
            minutes_1, team_1_name, competition_1, season_1, age_1, date_label_1, ax, side="left"
        )
        self._draw_subheader(
            minutes_2, team_2_name, competition_2, season_2, age_2, date_lable_2, ax, side="right"
        )
        self._plot_cutout(data["player_id"].iloc[0], ax, side="left")
        self._plot_cutout(data["player_id"].iloc[1], ax, side="right")

    def _plot_endnotes(self, ax: Axes, data: pd.DataFrame):
        template_name = data["Template Name"].iloc[0]
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        if self.SCOUTED_IMAGE_LOCATION:
            image = Image.open(urlopen(self.SCOUTED_IMAGE_LOCATION))
            image_aspect = image.size[1] / image.size[0]
            ax_aspect = get_aspect(ax)
            inset_scouted = ax.inset_axes([0.02, 4.6, 0.15, 0.15 / ax_aspect * image_aspect])
            inset_scouted.axis("off")
            inset_scouted.imshow(image)
            ax.text(
                0.02,
                8,
                "Graphic Design Inspired By",
                fontproperties=font_normal.prop,
                fontsize=8,
                ha="left",
                va="center",
                zorder=8,
            )
        string = "European Competition stats included where applicable"
        # replace the last comma with an and
        string = string[::-1].replace(",", "dna ", 1)[::-1]
        ax.text(
            0.02,
            0.02,
            string,
            ha="left",
            va="bottom",
            fontproperties=font_italic.prop,
            color=self.textcolor,
            fontsize=8,
        )
        template_color = self._template_color(template_name)
        if is_high_luminance(template_color):
            text_color = "black"
        else:
            text_color = "white"
        ax.text(
            0.98,
            6.5,
            template_name,
            ha="right",
            va="top",
            fontsize=8,
            color=text_color,
            bbox=dict(
                facecolor=self._template_color(template_name),
                edgecolor=self._template_color(template_name),
                boxstyle="round,pad=0.2",
            ),
        )
        ax.text(
            0.98,
            8.5,
            "Template",
            ha="right",
            va="top",
            fontsize=8,
            color="black",
            fontproperties=font_italic.prop,
        )
        ax.text(
            0.98,
            4.5,
            "Analysis and Implementation:\n@mclachbot and @ChicagoDmitry\nData from www.fbref.com",
            ha="right",
            va="top",
            fontsize=8,
            color="black",
            fontproperties=font_normal.prop,
        )

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = self._setup_figure()
        self._plot_radar(axes["radar"], data)
        self._plot_header(axes["title"], data, fig)
        self._plot_endnotes(axes["endnote"], data)
        return fig, axes
