"""
Various utility helper functions for matplotlib
"""
from matplotlib.axes import Axes


def get_aspect(ax: Axes) -> float:
    """
    Get the aspect ratio of an axes.
    From Stackoverflow post by askewchan:
    https://stackoverflow.com/questions/41597177/get-aspect-ratio-of-axes

    Args:
        ax (Axes): matplotlib axes

    Returns:
        float: aspect ratio, height/width
    """
    left_bottom, right_top = ax.get_position() * ax.figure.get_size_inches()
    width, height = right_top - left_bottom
    return height / width * ax.get_data_ratio()
