from PIL import Image, ImageDraw, ImageFont

def draw_centered_multiline_text(draw, text, center_x, center_y, font, fill="black", align="center"):
    """
    Draw multi-line text so that its bounding box is centered at (center_x, center_y).
    """
    # Measure total width/height of the multi-line text
    # For older Pillow versions, use draw.multiline_textsize(...) if draw.textbbox isn't available.
    bbox = draw.textbbox((0, 0), text, font=font, align=align, spacing=4)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate top-left corner so that the text is centered
    x = center_x - text_width / 2
    y = center_y - text_height / 2

    # Draw multiline text
    draw.multiline_text((x, y), text, font=font, fill=fill, align=align, spacing=4)

def create_a5_png_with_line_and_centered_text(
    img_path_top: str,
    img_path_bottom: str,
    output_path: str = "output.png"
):
    """
    Creates an A5 portrait PNG (~1748 x 2480 px):
      - Rotates both images 180° and places them in top/bottom halves.
      - Draws a horizontal line across the exact middle (y=1240).
      - Centers text in the top half and bottom half, with some gap around the line.
    """
    # A5 portrait ~1748 (width) x 2480 (height) at ~300 DPI
    A5_WIDTH = 1748
    A5_HEIGHT = 2480

    # Create a blank white canvas
    canvas = Image.new("RGB", (A5_WIDTH, A5_HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)

    half_height = A5_HEIGHT // 2  # ~1240

    # ---------------------------------------------------------
    # 1) Rotate images 180° and place them in top/bottom halves
    # ---------------------------------------------------------
    img_top = Image.open(img_path_top).rotate(180, expand=True)
    img_bottom = Image.open(img_path_bottom).rotate(180, expand=True)

    # For simplicity, let's resize each image so it fills most of the half
    # We can leave some space for text above/below the images
    # Example: each image gets 100 px from top/bottom for text in each half
    IMAGE_MARGIN = 100
    top_image_height = half_height - (2 * IMAGE_MARGIN)
    bottom_image_height = top_image_height  # same size for consistency

    # Resize images to (width=1748, height=top_image_height)
    img_top = img_top.resize((A5_WIDTH, top_image_height), Image.LANCZOS)
    img_bottom = img_bottom.resize((A5_WIDTH, bottom_image_height), Image.LANCZOS)

    # Paste top image in the top half, offset by IMAGE_MARGIN from the top
    canvas.paste(img_top, (0, IMAGE_MARGIN))

    # Paste bottom image in the bottom half, offset by IMAGE_MARGIN from the middle
    # The y-position for bottom image is half_height + IMAGE_MARGIN
    canvas.paste(img_bottom, (0, half_height + IMAGE_MARGIN))

    # ---------------------------------------------------------
    # 2) Draw a horizontal line in the middle
    # ---------------------------------------------------------
    # We'll draw from x=0 to x=A5_WIDTH at y=half_height
    line_y = half_height
    draw.line((0, line_y, A5_WIDTH, line_y), fill="black", width=3)

    # ---------------------------------------------------------
    # 3) Load fonts. We'll try Segoe Script. Fallback if missing.
    # ---------------------------------------------------------
    try:
        # Adjust path or filename if needed (e.g. "C:/Windows/Fonts/seguiscr.ttf")
        font_top = ImageFont.truetype("seguiscr.ttf", 18)
        font_bottom = ImageFont.truetype("seguiscr.ttf", 16)
    except OSError:
        # Fall back if not found
        font_top = ImageFont.load_default()
        font_bottom = ImageFont.load_default()

    # ---------------------------------------------------------
    # 4) Center text in top half and bottom half, with a gap from the middle line
    # ---------------------------------------------------------
    # Example text for top half: "Your Wedding Quest"
    # We'll place it near the vertical center of the top half,
    # but maybe 50 px above the line to give a gap.
    top_half_center_y = (line_y // 2)  # midpoint of the top half
    # Or if you want it near the line, do something like:
    # top_text_y = half_height - 100  # e.g. 100 px above the line

    # Let's do a multiline text: "Your Wedding Quest\nNicki & Tony Wedding\n13th December 2025"
    top_text = ""

    # We'll center it horizontally, and place it ~200 px above the line
    # so it doesn't collide with the line. Let's pick line_y - 200 as center.
    center_y_top_text = line_y - 200
    draw_centered_multiline_text(draw, top_text, A5_WIDTH/2, center_y_top_text, font_top)

    # Bottom half text: "Please Use The QR code\nto upload your images"
    # We'll place it around 200 px below the line. 
    bottom_text = ""
    center_y_bottom_text = line_y + 200
    draw_centered_multiline_text(draw, bottom_text, A5_WIDTH/2, center_y_bottom_text, font_bottom)

    # ---------------------------------------------------------
    # 5) Save output
    # ---------------------------------------------------------
    canvas.save(output_path)
    print(f"PNG created: {output_path}")


# Example usage
if __name__ == "__main__":
    create_a5_png_with_line_and_centered_text(
        img_path_top="./jukebox2/useful tools/wedding_logo_slightly_darker_gold.png",
        img_path_bottom="./jukebox2/useful tools/googleweddingphotos.png",
        output_path="front_a5.png"
    )
