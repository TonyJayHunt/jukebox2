import pytest
from PIL import Image, ImageDraw, ImageFont
import useful_tools.front as front

def test_draw_centered_multiline_text(tmp_path):
    img = Image.new("RGB", (200, 200), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    front.draw_centered_multiline_text(draw, "Hello\nWorld", 100, 100, font)
    # Just check it draws without error

def test_create_a5_png_with_line_and_centered_text(tmp_path):
    # Create dummy images
    img1 = tmp_path / "img1.png"
    img2 = tmp_path / "img2.png"
    Image.new("RGB", (100, 100), "blue").save(img1)
    Image.new("RGB", (100, 100), "red").save(img2)
    out = tmp_path / "out.png"
    front.create_a5_png_with_line_and_centered_text(str(img1), str(img2), str(out))
    assert out.exists()
