"""Small versions of the images, for lists such as the library. Made during build, offline."""
from pathlib import Path

from PIL import Image, ImageOps

# Longest side in pixels: the library shows them at about 56 px, so this stays sharp on high-density screens.
THUMBNAIL_SIZE = 240
THUMBNAIL_QUALITY = 80

def make_thumbnail(
    source: Path,
    target: Path,
    size: int = THUMBNAIL_SIZE
) -> None:
    """Writes a WebP of at most size × size pixels, upright and with its transparency.

    Raises OSError (or ValueError) if source is not an image Pillow can read.
    """
    with Image.open(source) as image:
        thumbnail = ImageOps.exif_transpose(image)
        thumbnail.thumbnail((size, size))
        has_alpha = "A" in thumbnail.getbands() or "transparency" in thumbnail.info
        thumbnail = thumbnail.convert("RGBA" if has_alpha else "RGB")
        target.parent.mkdir(parents = True, exist_ok = True)
        thumbnail.save(target, "WEBP", quality = THUMBNAIL_QUALITY)
