"""Render the page icon: a solid periwinkle disc, per the Ersilia design system.

The design system asks for a plain solid disc in a brand colour rather than the
old ring-and-dot mark, and the 2201x601 wordmark is the wrong shape for a favicon.
"""

import os

from PIL import Image, ImageDraw

PERIWINKLE = (108, 92, 231, 255)  # #6C5CE7, the app's interactive accent
SIZE = 256

root = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(root, "..", "assets", "favicon.png")

image = Image.new("RGBA", (SIZE * 4, SIZE * 4), (0, 0, 0, 0))
ImageDraw.Draw(image).ellipse((0, 0, SIZE * 4 - 1, SIZE * 4 - 1), fill=PERIWINKLE)
image.resize((SIZE, SIZE), Image.LANCZOS).save(target)
print("wrote {0} ({1}x{1})".format(os.path.relpath(target, root), SIZE))
