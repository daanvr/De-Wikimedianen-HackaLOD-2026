from pathlib import Path

from PIL import Image
import pytest

from siboga.thumbnails import THUMBNAIL_SIZE, make_thumbnail

def test_make_thumbnail_fits_in_square(tmp_path: Path):
    source = tmp_path / "groot.jpg"
    Image.new("RGB", (1600, 1200), "navy").save(source)
    target = tmp_path / "thumbs" / "groot.webp"
    make_thumbnail(source, target)
    with Image.open(target) as thumbnail:
        assert thumbnail.format == "WEBP"
        assert thumbnail.size == (THUMBNAIL_SIZE, 180)

def test_make_thumbnail_keeps_transparency(tmp_path: Path):
    source = tmp_path / "kat.png"
    Image.new("RGBA", (800, 800), (0, 0, 0, 0)).save(source)
    target = tmp_path / "kat.webp"
    make_thumbnail(source, target)
    with Image.open(target) as thumbnail:
        assert thumbnail.mode == "RGBA"
        assert thumbnail.getpixel((10, 10))[3] == 0

def test_make_thumbnail_rotates_upright(tmp_path: Path):
    source = tmp_path / "gedraaid.jpg"
    exif = Image.Exif()
    # Orientation 6: the camera was turned, the image must be rotated 90 degrees.
    exif[0x0112] = 6
    Image.new("RGB", (400, 200), "white").save(source, exif = exif)
    target = tmp_path / "gedraaid.webp"
    make_thumbnail(source, target)
    with Image.open(target) as thumbnail:
        assert thumbnail.size == (120, THUMBNAIL_SIZE)

def test_make_thumbnail_does_not_enlarge(tmp_path: Path):
    source = tmp_path / "klein.png"
    Image.new("L", (100, 50), 128).save(source)
    target = tmp_path / "klein.webp"
    make_thumbnail(source, target)
    with Image.open(target) as thumbnail:
        assert thumbnail.size == (100, 50)

def test_make_thumbnail_rejects_non_image(tmp_path: Path):
    source = tmp_path / "kapot.jpg"
    source.write_bytes(b"\xff\xd8\xff")
    with pytest.raises(OSError):
        make_thumbnail(source, tmp_path / "kapot.webp")
