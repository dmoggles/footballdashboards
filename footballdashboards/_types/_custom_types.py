"""
Defines custom types to be used for type hinting in the rest of the library
"""

from typing import Dict, Tuple, Union
from matplotlib.axes import Axes
from matplotlib.figure import Figure

PlotReturnType = Tuple[Figure, Union[Axes, Dict[str, Axes]]]
