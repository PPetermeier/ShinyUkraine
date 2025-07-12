"""Module for color manipulation utilities.

This module provides utilities for manipulating colors, particularly for
creating visual variations of existing colors in visualizations.
"""

import colorsys


def desaturate_color(hex_color: str, factor: float = 0.75) -> str:
    """Create a desaturated version of a hex color.

    This function takes a hex color and creates a lighter version by adjusting
    its HSL (Hue, Saturation, Lightness) values. Commonly used for creating
    secondary or background variations of primary colors in visualizations.

    Args:
        hex_color: Hex color string (e.g., '#FF0000' or 'FF0000')
        factor: Lightness adjustment factor. Values > 1 increase lightness.
            Default is 0.75.

    Returns:
        str: Desaturated color in hex format (e.g., '#FF8888')

    Example:
        >>> desaturate_color('#FF0000', 0.75)
        '#FF8888'
    """
    # Normalize hex color by removing '#' if present
    hex_color = hex_color.lstrip("#")

    # Convert hex to RGB (0-1 range)
    rgb: tuple[float, float, float] = tuple(
        int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4)
    )

    # Convert RGB to HSL, adjust lightness, convert back to RGB
    h_color, l_color, s_color = colorsys.rgb_to_hls(*rgb)
    rgb_desat = colorsys.hls_to_rgb(h_color, min(1, l_color * (1 + factor)), s_color)

    # Convert back to hex format
    return f"#{int(rgb_desat[0] * 255):02x}{int(rgb_desat[1] * 255):02x}{int(rgb_desat[2] * 255):02x}"
