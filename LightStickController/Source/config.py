

# HELPER TO SET RGB TO NORMALIZED TUPLE
def RGBA(red, green, blue, alpha=1.0):
    return ((1.0 / 255) * red), ((1.0 / 255) * green), ((1.0 / 255) * blue), alpha


class WIDGET_COLORS():
    SCREEN_BACKGROUND = (0.8, 0.8, 0.8, 1)

    WIDGET_HEADER_COLOR = (0.5, 0.5, 0.5, 1)

    WIDGET_BACKGROUND_DARK = (0.3, 0.3, 0.3, 1)
    WIDGET_BACKGROUND_LIGHT = (0.4, 0.4, 0.4, 1)
    WIDGET_GREY_LIGHT = (0.6, 0.6, 0.6, 0.7)
    WHITE = (1, 1, 1, 1)

    WIDGET_BPM_SCREEN_COLOR = RGBA(0, 111, 178)


class WIDGET_SIZES():
    SCREEN_PADDING = 2
    SCREEN_SPACING = 2

    WIDGET_BORDER = 2
    WIDGET_SPACING = 0