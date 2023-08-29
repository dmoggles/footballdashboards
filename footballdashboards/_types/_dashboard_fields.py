"""defines descriptors for dashboard fields"""
from typing import Any, Optional
from matplotlib.colors import is_color_like
import matplotlib.pyplot as plt


class DashboardField:
    """
    Simple descriptor for dashboard field with no validation

    """

    def __init__(self, description: str, default: Optional[Any] = None):
        self.name = None
        self.default = self._set_validate(default)
        self.description = description

    def __set_name__(self, owner, name):
        self.name = name

        if owner.__name__ not in owner.field_descriptor_list:
            owner.field_descriptor_list[owner.__name__] = []
        owner.field_descriptor_list[owner.__name__].append((name, self.description))

    def __set__(self, instance, value):
        value = self._set_validate(value)
        instance.__dict__[self.name] = value

    def __get__(self, instance, owner):
        return instance.__dict__.get(self.name, self.default)

    def __delete__(self, instance):
        del instance.__dict__[self.name]

    def _set_validate(self, value):
        return value

    def __str__(self) -> str:
        return f"self.__class__.__name__(default={self.default!r})"


class ColorField(DashboardField):
    """
    Descriptor for color field.

    Validates that the color is in fact a valid matplotlib color
    """

    def _set_validate(self, value):
        if value is not None and not is_color_like(value):
            raise ValueError(f"{value} is not a valid color")
        return value


class ColorMapField(DashboardField):
    """
    Descriptor for colormap field.

    Validates that the colormap is in fact a valid matplotlib colormap
    """

    def _set_validate(self, value):
        if value is not None and value not in plt.colormaps():
            raise ValueError(f"{value} is not a valid colormap")
        return value


class FigSizeField(DashboardField):
    """
    Descriptor for figure size field.  Must be a tuple of two floats

    """

    def _set_validate(self, value):
        if not isinstance(value, tuple):
            raise ValueError("figsize must be a tuple of two floats")
        if len(value) != 2:
            raise ValueError("figsize must be a tuple of two floats")
        if not all(isinstance(x, (float, int)) for x in value):
            raise ValueError("figsize must be a tuple of two floats")
        return value


class FloatListField(DashboardField):
    """
    Descriptor for float list field.  Must be a list of floats

    """

    def _set_validate(self, value):
        if not isinstance(value, list):
            raise ValueError("float list field must be a list")
        if not all(isinstance(x, (float, int)) for x in value):
            raise ValueError("float list field must be a list of floats")
        return value


class FontSizeField(DashboardField):
    """
    Descriptor for font size field.
    Must be a float greater than 8 (anything smaller is just impossible to read)

    """

    def _set_validate(self, value):
        if not isinstance(value, (float, int)):
            raise ValueError("fontsize must be a float")
        if value < 8:
            raise ValueError("fontsize must be greater than 8")
        return value


class DictField(DashboardField):
    """
    Descriptor for dictionary field.

    """

    def __init__(self, description: str, acceptable_keys: list, default: Optional[Any] = None):
        default = default or {}
        super().__init__(description, default)
        self.acceptable_keys = acceptable_keys

    def _set_validate(self, value):
        if not isinstance(value, dict):
            raise ValueError("dict field must be a dictionary")
        if not all(key in self.acceptable_keys for key in value.keys()):
            raise ValueError(f"dict field must have keys in {self.acceptable_keys}")
        return value


class NumOfItemsField(DashboardField):
    """
    Descriptor for number of items field.

    Must be an integer greater than 0

    """

    def _set_validate(self, value):
        if not isinstance(value, int):
            raise ValueError("num_of_items must be an integer")
        if value < 1:
            raise ValueError("num_of_items must be greater than 0")
        return value


class ColorListField(DashboardField):
    """
    Descriptor for color list field.

    Must be a list of valid matplotlib colors

    """

    def _set_validate(self, value):
        if not isinstance(value, list):
            raise ValueError("color list field must be a list")
        if not all(is_color_like(x) for x in value):
            raise ValueError("color list field must be a list of valid colors")
        return value
