import colorsys


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
