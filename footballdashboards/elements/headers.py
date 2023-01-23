"""
Functions for styling various headers on a given axis.
"""
from typing import Dict, Any
from matplotlib.axes import Axes
from footballdashboards.helpers.fonts import font_bold, font_italic


def simple_title_subtitle_header(
    axis: Axes,
    title: str,
    subtitle: str,
    title_kwargs: Dict[str, Any],
    subtitle_kwargs: Dict[str, Any],
):

    """
    Simple header with title and subtitle
    """
    axis.text(
        0.5,
        0.5,
        title,
        ha=title_kwargs.get("ha", "center"),
        va=title_kwargs.get("va", "center"),
        fontproperties=font_bold.prop,
        **title_kwargs
    )
    if subtitle:
        axis.text(
            0.5,
            -0.2,
            subtitle,
            ha=subtitle_kwargs.get("ha", "center"),
            va=subtitle_kwargs.get("va", "center"),
            fontproperties=font_italic.prop,
            **subtitle_kwargs
        )
