import numpy as np
from typing import Tuple
from enum import Enum

class ColourShade(Enum):
    LIGHT = 1
    DARK = 2

def is_light_or_dark(rgbColor: Tuple[float, float, float, float])->ColourShade:
    [r,g,b,_]=np.array(rgbColor)*255
    hsp = np.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
    if (hsp>127.5):
        return ColourShade.LIGHT
    else:
        return ColourShade.DARK