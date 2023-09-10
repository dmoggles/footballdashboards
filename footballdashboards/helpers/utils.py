import colorsys
import matplotlib.colors as mcolors


def color_name_to_rgb(color_name):
    try:
        rgb_tuple = mcolors.to_rgba(color_name)[:3]  # Extract the RGB values
        return tuple(int(x * 255) for x in rgb_tuple)  # Convert to 8-bit RGB
    except ValueError:
        raise ValueError("Invalid color name")


def get_complimentary_color(hex_color):
    # Convert hex color to RGB tuple
    hex_color = hex_color[1:]
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    # Convert RGB color to HSV tuple
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

    # Compute the hue of the complimentary color (180 degrees away)
    h_complimentary = (h + 0.5) % 1.0

    # Convert the HSV complimentary color to RGB tuple
    r_complimentary, g_complimentary, b_complimentary = colorsys.hsv_to_rgb(h_complimentary, s, v)

    # Convert the RGB complimentary color to hex string
    hex_complimentary = "#{:02x}{:02x}{:02x}".format(
        int(r_complimentary * 255), int(g_complimentary * 255), int(b_complimentary * 255)
    )
    return hex_complimentary


def is_high_luminance(color):
    # Convert the color to RGB format if it's in hexadecimal or other formats
    if color.startswith("#"):
        color = color[1:]
        color = tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))
    elif color.startswith("rgb"):
        color = color[color.index("(") + 1 : color.index(")")].split(",")
        color = tuple(int(channel.strip()) for channel in color)
    elif isinstance(color, str):
        color = color_name_to_rgb(color)
    # Extract the red, green, and blue channels
    if len(color) == 4:
        r, g, b, _ = color
    else:
        r, g, b = color

    # Calculate the relative luminance
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0

    # Decide whether the color is light or dark based on luminance
    if luminance > 0.5:
        return True
    else:
        return False
