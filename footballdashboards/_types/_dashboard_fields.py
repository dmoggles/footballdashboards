"""defines descriptors for dashboard fields"""
from matplotlib.colors import is_color_like


class ColorField:
    """
    Descriptor for color field.

    Validates that the color is in fact a valid matplotlib color
    """

    def __init__(self, default=None):
        self.name = None
        if default is not None:
            if not is_color_like(default):
                raise ValueError(f"{default} is not a valid color")
            self.default = default

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        if value is not None:

            if not is_color_like(value):
                raise ValueError(f"{value} is not a valid color")
        instance.__dict__[self.name] = value

    def __get__(self, instance, owner):
        return instance.__dict__.get(self.name, self.default)
