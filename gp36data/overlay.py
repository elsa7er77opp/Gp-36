"""Annotation overlays and contact sheets for human review.

Boxes are drawn without text tags on the image (a tag drawn above a box was what made the
``pothole_058`` box look as if it were on the CAUTION sign). Box numbers and file details are
written in a caption strip below each tile instead.
"""
from PIL import Image, ImageDraw, ImageFont

COLORS = {0: (255, 40, 40), 1: (30, 144, 255)}  # pothole red, speed bump blue
OTHER = (255, 215, 0)


def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def draw_boxes(im, boxes, class_colors=COLORS, number=True):
    """Return an RGB copy of im with boxes (cls, xc, yc, w, h normalised) drawn on it."""
    im = im.convert("RGB").copy()
    W, H = im.size
    d = ImageDraw.Draw(im)
    lw = max(2, round(max(W, H) / 400))
    f = _font(max(12, lw * 6))
    for k, b in enumerate(boxes, start=1):
        cls, xc, yc, w, h = b
        x1, y1, x2, y2 = (xc - w / 2) * W, (yc - h / 2) * H, (xc + w / 2) * W, (yc + h / 2) * H
        d.rectangle([x1, y1, x2, y2], outline=class_colors.get(cls, OTHER), width=lw)
        if number:  # small index inside the box's top-left corner
            d.text((x1 + lw + 1, y1 + lw), str(k), fill=class_colors.get(cls, OTHER), font=f,
                   stroke_width=max(1, lw // 2), stroke_fill=(0, 0, 0))
    return im


def tile(im, caption_lines, width=480, caption_px=16):
    """Scale an image to a fixed width and add a caption strip below it."""
    s = width / im.width
    im = im.resize((width, max(1, round(im.height * s))), Image.BILINEAR)
    cap_h = (caption_px + 4) * len(caption_lines) + 6
    out = Image.new("RGB", (width, im.height + cap_h), (25, 25, 25))
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    f = _font(caption_px)
    for i, line in enumerate(caption_lines):
        d.text((4, im.height + 3 + i * (caption_px + 4)), line, fill=(235, 235, 235), font=f)
    return out


def contact_sheet(tiles, cols=4, pad=6, title=None):
    """Arrange tiles in a grid (row height = tallest tile in the row)."""
    if not tiles:
        raise ValueError("no tiles")
    rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
    col_w = max(t.width for t in tiles)
    title_h = 34 if title else 0
    heights = [max(t.height for t in r) for r in rows]
    sheet = Image.new("RGB", (cols * (col_w + pad) + pad, sum(heights) + pad * (len(rows) + 1) + title_h), (60, 60, 60))
    if title:
        ImageDraw.Draw(sheet).text((pad, 6), title, fill=(255, 255, 255), font=_font(22))
    y = pad + title_h
    for r, h in zip(rows, heights):
        x = pad
        for t in r:
            sheet.paste(t, (x, y))
            x += col_w + pad
        y += h + pad
    return sheet
