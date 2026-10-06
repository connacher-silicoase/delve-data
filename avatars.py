"""Shared physical-size circular avatars and packed user labels."""
from matplotlib.offsetbox import DrawingArea, HPacker, OffsetImage, VPacker
from PIL import Image, ImageDraw, ImageOps

from chart_layout import text_box, measure, wrapped_text

SOURCE_PX = 128


def avatar_image(folder, handle):
    path = next(folder.glob(f'{handle}.*'), None)
    if path:
        with Image.open(path) as source:
            image = ImageOps.fit(source.convert('RGBA'), (SOURCE_PX, SOURCE_PX))
    else:
        image = Image.new('RGBA', (SOURCE_PX, SOURCE_PX), '#084a91')
    mask = Image.new('L', image.size)
    ImageDraw.Draw(mask).ellipse((0, 0, SOURCE_PX - 1, SOURCE_PX - 1), fill=255)
    image.putalpha(mask)
    return image


def avatar_box(folder, handle, diameter=18):
    return OffsetImage(avatar_image(folder, handle), zoom=diameter / SOURCE_PX)


def short_name(handle):
    return handle[-8:] if handle.startswith('did:') else handle.removesuffix('.delve.town')


def user_box(fig, folder, handle, diameter=14):
    return HPacker(children=[avatar_box(folder, handle, diameter), wrapped_text(fig, short_name(handle), 8, 90)],
                   align='center', pad=0, sep=4)


def pair_boxes(fig, folder, pairs):
    rows = [[user_box(fig, folder, handle) for handle in pair] for pair in pairs]
    widths = [max(measure(fig, row[column])[0] for row in rows) for column in (0, 1)]
    aligned = [[HPacker(children=[box, DrawingArea(max(0, widths[column] - measure(fig, box)[0]), 0)],
                         align='center', pad=0, sep=0)
                for column, box in enumerate(row)] for row in rows]
    return [HPacker(children=[row[0], text_box('↔', 10, '0.5'), row[1]],
                    align='center', pad=0, sep=10) for row in aligned]



def poster_box(folder, handle, reply_fraction):
    return VPacker(children=[avatar_box(folder, handle, 22), text_box(short_name(handle), 8),
                             text_box(f'{reply_fraction:.0%} replies', 6)],
                   align='center', pad=0, sep=3)
