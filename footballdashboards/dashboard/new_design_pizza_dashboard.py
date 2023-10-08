import pandas as pd
import os
from matplotlib.axes import Axes
from footballdashboards.dashboard.pizzadashboard import PizzaDashboard
from footballdashboards.helpers.mclachbot_helpers import (
    McLachBotBadgeService,
    TeamColorHelper,
    CachedPlayerImageHelper,
)
from footballdashboards.helpers.matplotlib import get_aspect
from scipy.ndimage import rotate
from footballdashboards.helpers.fonts import font_europa, font_normal, font_italic
from footballdashboards.helpers.formatters import smartest_name_formatter_yet
from footballdashboards.helpers.utils import is_high_luminance
from footballdashboards._types._custom_types import PlotReturnType
from matplotlib.figure import Figure
from matplotlib.cm import get_cmap
from PIL import Image
import numpy as np
from urllib.request import urlopen


class NewDesignPizzaDashboard(PizzaDashboard):
    PLAYER_IMAGE_CACHE_URL = None
    PRESERVE_FULLSIZE_CUTOUT = False
    SCOUTED_IMAGE_LOCATION = None

    def _template_color(self):
        templates = {
            "CMPizza": "blue",
            "CBPizza": "green",
            "FBPizza": "orange",
            "FWPizza": "red",
            "AMPizza": "pink",
            "ATTPizza": "grey",
            "GKPizza": "purple",
            "TargetmanPizza": "black",
        }
        return templates[self.datasource_name]

    def _template_name(self):
        templates = {
            "CMPizza": "Midfielder",
            "CBPizza": "Centre Back",
            "FBPizza": "Full Back",
            "FWPizza": "Forward",
            "AMPizza": "Attacking Midfielder/Winger",
            "ATTPizza": "Combined Fwd/AM",
            "GKPizza": "Goalkeeper",
            "TargetmanPizza": "Targetman Forward",
        }
        return templates[self.datasource_name]

    def _setup_figure(self):
        fig = Figure(figsize=(6.75, 7.8), dpi=100, facecolor=self.facecolor)
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)

        axes = {}
        axes["pizza"] = fig.add_axes(
            (0.1, 0.01, 0.8, 0.80), projection="polar", facecolor=self.facecolor, aspect="equal"
        )
        axes["title"] = fig.add_axes(
            (0, 0.82, 1.0, 0.17), facecolor=self.facecolor, xmargin=0, ymargin=0, zorder=1
        )
        axes["title"].set_xlim(0, 1)
        axes["title"].set_ylim(0, 1)

        axes["title"].axis("off")
        axes["title"].set_yticks([])
        axes["title"].set_xticks([])

        axes["endnote"] = fig.add_axes((0, 0, 1, 0.01), facecolor=self.facecolor)
        axes["endnote"].axis("off")

        return fig, axes

    def _plot_data(self, data: pd.DataFrame) -> PlotReturnType:
        fig, axes = self._setup_figure()
        self._plot_pizza(data, axes["pizza"])
        self._plot_title(data, axes["title"], fig)
        self._plot_endnote(data, axes["endnote"])
        return fig, axes

    def _plot_endnote(self, data: pd.DataFrame, ax: Axes) -> Axes:
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
                "Graphic Design By",
                fontproperties=font_normal.prop,
                fontsize=8,
                ha="left",
                va="center",
                zorder=8,
            )

        try:
            comparable = [c.strip() for c in data["All Competitions"].values[0].split(",")]
            string = "Compared to qualifying players in\n" + ", ".join(comparable)
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
        except:
            print("No comparable leagues found")

        # ax.text(0.8, 8, "Template: ", ha="left", va="center", fontsize=8)
        template_color = self._template_color()
        if is_high_luminance(template_color):
            text_color = "black"
        else:
            text_color = "white"
        ax.text(
            0.98,
            6.5,
            self._template_name(),
            ha="right",
            va="top",
            fontsize=8,
            color=text_color,
            bbox=dict(
                facecolor=self._template_color(),
                edgecolor=self._template_color(),
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

    def _place_team_logo(self, team: str, league, ax: Axes, fig: Figure):
        img = McLachBotBadgeService().team_badge(league, team)
        img = np.array(list(img.convert('RGBA').getdata())).reshape(img.height, img.width, 4)
        rotated_img = rotate(img, 10, reshape=True)
        rotated_img = rotated_img[
            int(rotated_img.shape[0] / 5) : rotated_img.shape[0],
            int(rotated_img.shape[1] / 5) : rotated_img.shape[1],
        ]
        fig_aspect = fig.get_figheight() / fig.get_figwidth()
        img_size = 0.2
        ax = fig.add_axes([0, 1 - img_size, img_size * fig_aspect, img_size], zorder=0.1)
        ax.axis("off")
        ax.imshow(rotated_img, alpha=0.2)

    def _draw_line(self, team_name: str, league_name: str, ax: Axes):
        color = TeamColorHelper().get_colours(league_name, team_name)
        if color is None or color[0] == "#bbbbbb":
            color = get_cmap(self.slice_colormap)(0.8)
        else:
            color = color[0]
        ax.plot([0.04, 0.96], [0.0, 0.0], lw=7, color=color, zorder=10)

    def _draw_name(self, player_name: str, ax: Axes):
        ax.text(
            0.06,
            0.6,
            smartest_name_formatter_yet(player_name),
            fontproperties=font_europa.prop,
            fontsize=38,
            ha="left",
            va="center",
            zorder=10,
        )

    def _format_season(self, season, league_name):
        if league_name in ["MLS", "Brasilian Serie A", "NWSL", "Argentine Primera", "World Cup"]:
            return f"{season} season"
        else:
            return f"{season}/{str(season+1)[-2:]} season"

    def _draw_subheader(
        self, minutes: str, team_name: str, league_name: str, season: str, age: str, ax: Axes
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
        ax.text(
            0.05,
            0.25,
            full_str1,
            fontproperties=font_normal.prop,
            fontsize=12,
            ha="left",
            va="bottom",
            zorder=10,
        )
        ax.text(
            0.05,
            0.1,
            full_str2,
            fontproperties=font_normal.prop,
            fontsize=12,
            ha="left",
            va="bottom",
            zorder=10,
        )

    def _plot_cutout(self, player_id: str, ax: Axes):
        aspect = get_aspect(ax)
        insert_ax = ax.inset_axes([1 - aspect - 0.04, 0, aspect, 1])
        insert_ax.axis("off")
        img = CachedPlayerImageHelper(self.PLAYER_IMAGE_CACHE_URL).get_player_image(player_id)
        if img is None:
            return
        img = np.array(list(img.convert('RGBA').getdata())).reshape(img.height, img.width, 4)
        
        img = np.array(img)
        if not self.PRESERVE_FULLSIZE_CUTOUT:
            img = img[
                int(img.shape[0] * 0.0) : int(img.shape[0] * 0.5),
                int(img.shape[1] * 0.25) : int(img.shape[1] * 0.75),
            ]
        insert_ax.imshow(img, alpha=1)

    def _plot_title(self, data: pd.DataFrame, ax: Axes, fig: Figure) -> Axes:
        team_image = data["image_team"].unique()[0]
        league_image = data["image_league"].unique()[0]
        player_name = data["Player"].unique()[0]
        minutes = data["Minutes"].unique()[0]
        team_name = data["Team"].unique()[0]
        league_name = data["Competition"].unique()[0]
        season = data["Season"].unique()[0]
        player_id = data["player_id"].unique()[0]
        age = data["Age"].unique()[0]
        self._place_team_logo(team_image, league_image, ax, fig)
        self._draw_line(team_image, league_image, ax)
        self._draw_name(player_name, ax)
        self._draw_subheader(minutes, team_name, league_name, season, age, ax)
        self._plot_cutout(player_id, ax)
