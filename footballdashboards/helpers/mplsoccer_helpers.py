"""
Some helper functions for working with mplsoccer.  Some of these contained code modified and adapted from mplsoccer.
"""

from matplotlib.figure import Figure
import numpy as np
from mplsoccer.pitch import Pitch
import numpy as np
from scipy.stats import binned_statistic_2d
from scipy.ndimage import gaussian_filter, zoom
from dataclasses import asdict
from mplsoccer.heatmap import _nan_safe, BinnedStatisticResult


def get_ax_size(ax, fig):
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    width *= fig.dpi
    height *= fig.dpi
    return width, height


def bin_statistic(
    x,
    y,
    values=None,
    dim=None,
    statistic="count",
    bins=(5, 4),
    normalize=False,
    standardized=False,
    gaussian_filter_value=None,
    zoom_value=None,
):
    """Calculates binned statistics using scipy.stats.binned_statistic_2d.

    This method automatically sets the range, changes the scipy defaults,
    and outputs the grids and centers for plotting.

    The default statistic has been changed to count instead of mean.
    The default bins have been set to (5,4).

    Parameters
    ----------
    x, y, values : array-like or scalar.
        Commonly, these parameters are 1D arrays.
        If the statistic is 'count' then values are ignored.
    dim : mplsoccer pitch dimensions
        One of FixedDims, MetricasportsDims, VariableCenterDims, or CustomDims.
        Automatically populated when using Pitch/ VerticalPitch class
    statistic : string or callable, optional
        The statistic to compute (default is 'count').
        The following statistics are available: 'count' (default),
        'mean', 'std', 'median', 'sum', 'min', 'max', 'circmean' or a user-defined function. See:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binned_statistic_2d.html
    bins : int or [int, int] or array_like or [array, array], optional
        The bin specification.
          * the number of bins for the two dimensions (nx = ny = bins),
          * the number of bins in each dimension (nx, ny = bins),
          * the bin edges for the two dimensions (x_edge = y_edge = bins),
          * the bin edges in each dimension (x_edge, y_edge = bins).
            If the bin edges are specified, the number of bins will be,
            (nx = len(x_edge)-1, ny = len(y_edge)-1).
    normalize : bool, default False
        Whether to normalize the statistic by dividing by the total.
    standardized : bool, default False
        Whether the x, y values have been standardized to the
        'uefa' pitch coordinates (105m x 68m)
    gaussian_filter_value : float, default None
        The standard deviation for the Gaussian kernel. If None, no filtering is performed.
    zoom_value : float, default None
        The zoom factor. If None, no zooming is performed.

    Returns
    -------
    bin_statistic : dict.
        The keys are 'statistic' (the calculated statistic),
        'x_grid' and 'y_grid (the bin's edges), cx and cy (the bin centers)
        and 'binnumber' (the bin indices each point belongs to).
        'binnumber' is a (2, N) array that represents the bin in which the observation falls
        if the observations falls outside the pitch the value is -1 for the dimension. The
        binnumber are zero indexed and start from the top and left handside of the pitch.

    Examples
    --------
    >>> from mplsoccer import Pitch
    >>> import numpy as np
    >>> pitch = Pitch(line_zorder=2, pitch_color='black')
    >>> fig, ax = pitch.draw()
    >>> x = np.random.uniform(low=0, high=120, size=100)
    >>> y = np.random.uniform(low=0, high=80, size=100)
    >>> stats = pitch.bin_statistic(x, y)
    >>> pitch.heatmap(stats, edgecolors='black', cmap='hot', ax=ax)
    """
    x = np.ravel(x)
    y = np.ravel(y)
    if x.size != y.size:
        raise ValueError("x and y must be the same size")
    statistic = _nan_safe(statistic)
    if (values is None) & (statistic == "count"):
        values = x
    if (values is None) & (statistic != "count"):
        raise ValueError("values on which to calculate the statistic are missing")
    if standardized:
        pitch_range = [[0, 105], [0, 68]]
    elif dim.invert_y:
        pitch_range = [[dim.left, dim.right], [dim.top, dim.bottom]]
        y = dim.bottom - y
    else:
        pitch_range = [[dim.left, dim.right], [dim.bottom, dim.top]]
    statistic, x_edge, y_edge, binnumber = binned_statistic_2d(
        x, y, values, statistic=statistic, bins=bins, range=pitch_range, expand_binnumbers=True
    )

    if gaussian_filter_value is not None:
        statistic = gaussian_filter(statistic, gaussian_filter_value)
    if zoom_value is not None:
        statistic = zoom(statistic, zoom_value)
        x_edge = np.linspace(x_edge[0], x_edge[-1], int(bins[0] * zoom_value) + 1)
        y_edge = np.linspace(y_edge[0], y_edge[-1], int(bins[1] * zoom_value) + 1)
        # Determine the bin indices in the new grid for each data point
        x_bin_indices = np.digitize(x, x_edge) - 1  # `-1` to match zero-based indexing
        y_bin_indices = np.digitize(y, y_edge) - 1
        binnumber = np.array([x_bin_indices, y_bin_indices])

    statistic = np.flip(statistic.T, axis=0)
    if statistic.ndim == 3:
        num_y, num_x, _ = statistic.shape
    else:
        num_y, num_x = statistic.shape
    if normalize:
        statistic = statistic / statistic.sum()
    binnumber[1, :] = num_y - binnumber[1, :] + 1
    x_grid, y_grid = np.meshgrid(x_edge, y_edge)
    cx, cy = np.meshgrid(x_edge[:-1] + 0.5 * np.diff(x_edge), y_edge[:-1] + 0.5 * np.diff(y_edge))

    if not dim.invert_y or standardized is not False:
        y_grid = np.flip(y_grid, axis=0)
        cy = np.flip(cy, axis=0)

    # if outside the pitch set the bin number to minus one
    # else zero index the results by removing one
    mask_x_out = np.logical_or(binnumber[0, :] == 0, binnumber[0, :] == num_x + 1)
    binnumber[0, mask_x_out] = -1
    binnumber[0, ~mask_x_out] = binnumber[0, ~mask_x_out] - 1

    mask_y_out = np.logical_or(binnumber[1, :] == 0, binnumber[1, :] == num_y + 1)
    binnumber[1, mask_y_out] = -1
    binnumber[1, ~mask_y_out] = binnumber[1, ~mask_y_out] - 1
    inside = np.logical_and(~mask_x_out, ~mask_y_out)
    return asdict(
        BinnedStatisticResult(statistic, x_grid, y_grid, cx, cy, binnumber=binnumber, inside=inside)
    )


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
