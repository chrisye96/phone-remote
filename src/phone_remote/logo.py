"""The Phone Remote logo: a play button whose sloping edges bow outward, sending out signal arcs.

One description of the shapes feeds every output: SVG for the web page, PNG through Pillow for
home screen icons, the tray and the Windows .ico (scripts/build-logo.py writes the files).
Coordinates are on a 100 x 100 grid, y pointing down, angles in degrees clockwise from 3 o'clock.
"""
import math

TILE, PLAY, SIGNAL = "#10233a", "#ffffff", "#38e1d0"

# FULL is the logo from 48 px up. SMALL is for 16 and 32 px: one thicker arc, a smaller play
# button further from it, so the gap still shows when each unit is a fraction of a pixel.
FULL = {"play": [(27, 43), (27, 71), (50, 57)], "bulge": 34, "play_width": 6,
        "arcs": [((50.5, 56), 20, -74, -14), ((50.5, 56), 34.6, -77.6, -13.4)], "arc_width": 6.5}
SMALL = {"play": [(26.5, 44), (26.5, 70), (47, 57)], "bulge": 31, "play_width": 7.5,
         # Turned 12 degrees further up than FULL's arcs, so it sits square to the play button's upper edge
         # (whose outward normal points at -57.6) and its right end does not droop
         "arcs": [((47, 57), 26, -89.6, -25.4)], "arc_width": 10.5}


def _point(centre, radius, degrees):
    a = math.radians(degrees)
    return centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a)


def _bow_centre(p, q, radius):
    # Centre of the circle through p and q that makes the edge p -> q bow outward (clockwise on screen)
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    dx, dy = q[0] - p[0], q[1] - p[1]
    half = math.hypot(dx, dy) / 2
    away = math.sqrt(radius * radius - half * half) / (2 * half)
    return mx - dy * away, my + dx * away


def _play_outline(design, steps=24):
    """Points around the play button: the two sloping edges as arcs, the upright edge straight."""
    top, bottom, tip = design["play"]
    points = []
    for p, q in ((top, tip), (tip, bottom)):
        c = _bow_centre(p, q, design["bulge"])
        a0 = math.atan2(p[1] - c[1], p[0] - c[0])
        a1 = math.atan2(q[1] - c[1], q[0] - c[0])
        if a1 < a0:
            a1 += 2 * math.pi
        points += [(c[0] + design["bulge"] * math.cos(a0 + (a1 - a0) * i / steps),
                    c[1] + design["bulge"] * math.sin(a0 + (a1 - a0) * i / steps)) for i in range(steps)]
    return points + [bottom]


def svg(design=FULL, bleed=False):
    """The logo as an SVG document. bleed fills the whole square, for icons the system rounds itself."""
    def n(v):
        return ("%.2f" % v).rstrip("0").rstrip(".")
    top, bottom, tip = design["play"]
    r = n(design["bulge"])
    tile = ('<rect width="100" height="100" fill="%s"/>' % TILE if bleed else
            '<rect x="4" y="4" width="92" height="92" rx="24" fill="%s"/>' % TILE)
    play = ('<path d="M%s %s A%s %s 0 0 1 %s %s A%s %s 0 0 1 %s %s Z" fill="%s" stroke="%s" stroke-width="%s" '
            'stroke-linejoin="round"/>' % (n(top[0]), n(top[1]), r, r, n(tip[0]), n(tip[1]), r, r,
                                           n(bottom[0]), n(bottom[1]), PLAY, PLAY, n(design["play_width"])))
    arcs = ""
    for centre, radius, start, end in design["arcs"]:
        (x0, y0), (x1, y1) = _point(centre, radius, start), _point(centre, radius, end)
        arcs += ('<path d="M%s %s A%s %s 0 0 1 %s %s" fill="none" stroke="%s" stroke-width="%s" '
                 'stroke-linecap="round"/>' % (n(x0), n(y0), n(radius), n(radius), n(x1), n(y1),
                                               SIGNAL, n(design["arc_width"])))
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">%s%s%s</svg>\n' % (tile, play, arcs)


def render(size, design=FULL, bleed=False):
    """The logo as a Pillow RGBA image, size x size pixels. Drawn 8 times larger, then scaled down for smooth edges."""
    from PIL import Image, ImageDraw  # only needed here, so the web side works without Pillow

    big = size * 8
    k = big / 100
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if bleed:
        draw.rectangle((0, 0, big, big), fill=TILE)
    else:
        draw.rounded_rectangle((4 * k, 4 * k, 96 * k, 96 * k), radius=24 * k, fill=TILE)

    def dot(x, y, width, colour):
        draw.ellipse((x * k - width * k / 2, y * k - width * k / 2, x * k + width * k / 2, y * k + width * k / 2),
                     fill=colour)

    outline = [(x * k, y * k) for x, y in _play_outline(design)]
    draw.polygon(outline, fill=PLAY)
    draw.line(outline + [outline[0]], fill=PLAY, width=round(design["play_width"] * k), joint="curve")
    for x, y in design["play"]:  # round corners, like stroke-linejoin="round"
        dot(x, y, design["play_width"], PLAY)
    width = design["arc_width"]
    for (cx, cy), radius, start, end in design["arcs"]:
        outer = radius + width / 2  # Pillow draws an arc's width inward from its box
        draw.arc(((cx - outer) * k, (cy - outer) * k, (cx + outer) * k, (cy + outer) * k), start, end,
                 fill=SIGNAL, width=round(width * k))
        for degrees in (start, end):  # round ends, like stroke-linecap="round"
            dot(*_point((cx, cy), radius, degrees), width, SIGNAL)
    return image.resize((size, size), Image.LANCZOS)


def for_size(size):
    """The design that reads best at this many pixels."""
    return SMALL if size <= 32 else FULL
