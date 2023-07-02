"""
Helpers for getting some standardized fonts
that are attached with this library for use in
matplotlib plots

"""

import os
import matplotlib.font_manager as fm


def get_path(file_name: str) -> str:
    """
    Function that gets the path to a font file

    Args:
        file_name (str): Name of the font file

    Returns:
        str: Path to the font file
    """
    return os.path.join(os.path.dirname(__file__), "../..", "font_files", file_name)


class FontManagerLocal:
    """
    Class that manages a font file
    """

    def __init__(self, path):
        self._prop = fm.FontProperties(fname=path)

    @property
    def prop(self) -> fm.FontProperties:
        """
        Property that returns the font properties

        Returns:
            fm.FontProperties: Font properties

        """
        return self._prop


font_normal = FontManagerLocal(
    get_path("roboto_normal.ttf"),
)
font_italic = FontManagerLocal(get_path("roboto_italic.ttf"))
font_bold = FontManagerLocal(
    get_path("roboto_bold.ttf"),
)

font_mono = FontManagerLocal(
    get_path("roboto_mono.ttf"),
)
font_varsity = FontManagerLocal(
    get_path("VarsityTeam-Bold.otf"),
)
