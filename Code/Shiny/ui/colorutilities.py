import colorsys

def desaturate_color(hex_color, factor=0.75):
    """Convert hex color to a desaturated version for 'To be Allocated' bars"""
    # Convert hex to RGB
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
   
    # Convert RGB to HSL, reduce lightness, convert back to RGB
    r, g, b = rgb
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    rgb_desat = colorsys.hls_to_rgb(h, min(1, l * (1 + factor)), s)
   
    # Convert back to hex
    return '#{:02x}{:02x}{:02x}'.format(
        int(rgb_desat[0] * 255),
        int(rgb_desat[1] * 255),
        int(rgb_desat[2] * 255)
    )
