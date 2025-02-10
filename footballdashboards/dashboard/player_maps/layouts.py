from typing import Dict, Any
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from mplsoccer.pitch import Pitch, VerticalPitch
from footballdashboards.dashboard.player_maps.plot_builder import GraphicComponents

def full_pitch_layout(config:Dict[str, Any])->GraphicComponents:
    fig = Figure(
        figsize=(8,11),
        facecolor = config['pitch_color']
    )
    axes = fig.subplot_mosaic(
        [
            ["header", "header"],
            ["pitch", "data_panel"],
            ["bottom", "bottom"]

        ],
        gridspec_kw={
            "height_ratios": [1, 6, 0.1],
            "width_ratios": [4, 1]
        }
    )
    for ax in axes.values():
        ax.axis(config['show_axis'])
        ax.set_xlim(0,1)
        ax.set_ylim(0,1)
    pitch = VerticalPitch(pitch_type="opta", pitch_color=config['pitch_color'], line_color=config['line_color'], linewidth=1)
    pitch.draw(ax=axes['pitch'])
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
    return GraphicComponents(fig, axes, {"pitch": pitch})
