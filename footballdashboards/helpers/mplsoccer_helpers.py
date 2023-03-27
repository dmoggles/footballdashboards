"""
Some helper functions for working with mplsoccer.  Some of these contained code modified and adapted from mplsoccer.
"""

from matplotlib.figure import Figure
import numpy as np
from mplsoccer.pitch import Pitch

def get_ax_size(ax, fig):
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    width *= fig.dpi
    height *= fig.dpi
    return width, height

def make_grid(
    pitch: Pitch,
    figheight=9,
    nrows=1,
    ncols=1,
    left=None,
    grid_width=0.95,
    bottom=None,
    endnote_height=0.065,
    endnote_space=0.01,
    grid_height=0.715,
    title_space=0.01,
    title_height=0.15,
    space=0.05,
    axis=True,
):  # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
    """A helper to create a grid of pitches in a specified location
    Parameters
    ----------
    figheight : float, default 9
        The figure height in inches.
    nrows, ncols : int, default 1
        Number of rows/columns of pitches in the grid.
    left : float, default None
        The location of the left hand side of the axes in fractions of the figure width.
        The default of None places the axes in the middle of the figure.
    grid_width : float, default 0.95
        The width of the pitch grid in fractions of the figure width.
        The default is the grid is 95% of the figure width.
    bottom : float, default None
        The location of the bottom endnote axes in fractions of the figure height.
        The default of None places the axes in the middle of the figure.
        If the endnote_height=0 then the pitch grid is located at the bottom coordinate instead.
    endnote_height: float, default 0.065
        The height of the endnote axes in fractions of the figure height.
        The default is the endnote is 6.5% of the figure height.
        If endnote_height=0, then the endnote axes is not plotted.
    endnote_space : float, default 0.01
        The space between the pitch grid and endnote axis in fractions of the figure height.
        The default space is 1% of the figure height.
        If endnote_height=0, then the endnote_space is set to zero.
    grid_height : float, default 0.715
        The height of the pitch grid in fractions of the figure height.
        The default is the grid height is 71.5% of the figure height.
    title_space : float, default 0.01
        The space between the pitch grid and title axis in fractions of the figure height.
        The default space is 1% of the figure height.
        If title_height=0, then the title_space is set to zero.
    title_height : float, default 0.15
        The height of the title axis in fractions of the figure height.
        The default is the title axis is 15% of the figure height.
        If title_height=0, then the title axes is not plotted.
    space : float, default 0.05
        The total amount of the grid height reserved for spacing between the pitch axes.
        Expressed as a fraction of the grid_height. The default is 5% of the grid height.
        The spacing across the grid width is automatically calculated to maintain even spacing.
    axis : bool, default True
        Whether the endnote and title axes are 'on'.
    Returns
    -------
    fig : matplotlib.figure.Figure
    axs : dict[label, Axes]
        A dictionary mapping the labels to the Axes objects.
        The possible keys are 'pitch', 'title', and 'endnote'.
    Examples
    --------
    >>> from mplsoccer import Pitch
    >>> pitch = Pitch()
    >>> fig, axs = pitch.grid(nrows=3, ncols=3, grid_height=0.7, figheight=14)
    """
    if left is None:
        left = (1 - grid_width) / 2

    if title_height == 0:
        title_space = 0

    if endnote_height == 0:
        endnote_space = 0

    error_msg_height = (
        "The axes extends past the figure height. "
        "Reduce one of the bottom, endnote_height, endnote_space, grid_height, "
        "title_space or title_height so the total is ≤ 1."
    )
    error_msg_width = (
        "The grid axes extends past the figure width. "
        "Reduce one of the grid_width or left so the total is ≤ 1."
    )

    axes_height = endnote_height + endnote_space + grid_height + title_space + title_height
    if axes_height > 1:
        raise ValueError(error_msg_height)

    if bottom is None:
        bottom = (1 - axes_height) / 2

    if bottom + axes_height > 1:
        raise ValueError(error_msg_height)

    if grid_width + left > 1:
        raise ValueError(error_msg_width)

    # calculate the figure width
    if (nrows > 1) and (ncols > 1):
        figwidth = (
            figheight
            * grid_height
            / grid_width
            * (
                ((1 - space) * pitch.ax_aspect * ncols / nrows)
                + (space * (ncols - 1) / (nrows - 1))
            )
        )
        individual_space_height = grid_height * space / (nrows - 1)
        individual_space_width = individual_space_height * figheight / figwidth
        individual_pitch_height = grid_height * (1 - space) / nrows

    elif (nrows > 1) and (ncols == 1):
        figwidth = grid_height * figheight / grid_width * (1 - space) * pitch.ax_aspect / nrows
        individual_space_height = grid_height * space / (nrows - 1)
        individual_space_width = 0
        individual_pitch_height = grid_height * (1 - space) / nrows

    elif (nrows == 1) and (ncols > 1):
        figwidth = grid_height * figheight / grid_width * (space + pitch.ax_aspect * ncols)
        individual_space_height = 0
        individual_space_width = grid_height * space * figheight / figwidth / (ncols - 1)
        individual_pitch_height = grid_height

    else:  # nrows=1, ncols=1
        figwidth = grid_height * pitch.ax_aspect * figheight / grid_width
        individual_space_height = 0
        individual_space_width = 0
        individual_pitch_height = grid_height

    individual_pitch_width = individual_pitch_height * pitch.ax_aspect * figheight / figwidth

    bottom_coordinates = np.tile(
        individual_space_height + individual_pitch_height, reps=nrows - 1
    ).cumsum()
    bottom_coordinates = np.insert(bottom_coordinates, 0, 0.0)
    bottom_coordinates = np.repeat(bottom_coordinates, ncols)
    grid_bottom = bottom + endnote_height + endnote_space
    bottom_coordinates = bottom_coordinates + grid_bottom
    bottom_coordinates = bottom_coordinates[::-1]

    left_coordinates = np.tile(
        individual_space_width + individual_pitch_width, reps=ncols - 1
    ).cumsum()
    left_coordinates = np.insert(left_coordinates, 0, 0.0)
    left_coordinates = np.tile(left_coordinates, nrows)
    left_coordinates = left_coordinates + left

    fig = Figure(figsize=(figwidth, figheight), dpi=100)
    axs = []
    for idx, bottom_coord in enumerate(bottom_coordinates):
        axs.append(
            fig.add_axes(
                (
                    left_coordinates[idx],
                    bottom_coord,
                    individual_pitch_width,
                    individual_pitch_height,
                )
            )
        )
        pitch.draw(ax=axs[idx])
    axs = np.squeeze(np.array(axs).reshape((nrows, ncols)))
    if axs.size == 1:
        axs = axs.item()

    left_pad = (
        np.abs(pitch.visible_pitch - pitch.extent)[0] / np.abs(pitch.extent[1] - pitch.extent[0])
    ) * individual_pitch_width
    right_pad = (
        np.abs(pitch.visible_pitch - pitch.extent)[1] / np.abs(pitch.extent[1] - pitch.extent[0])
    ) * individual_pitch_width
    title_left = left + left_pad
    title_width = grid_width - left_pad - right_pad

    result_axes = {"pitch": axs}

    if title_height > 0:
        ax_title = fig.add_axes(
            (
                title_left,
                grid_bottom + grid_height + title_space,
                title_width,
                title_height,
            )
        )
        if axis is False:
            ax_title.axis("off")
        result_axes["title"] = ax_title

    if endnote_height > 0:
        ax_endnote = fig.add_axes((title_left, bottom, title_width, endnote_height))
        if axis is False:
            ax_endnote.axis("off")
        result_axes["endnote"] = ax_endnote

    return fig, result_axes
