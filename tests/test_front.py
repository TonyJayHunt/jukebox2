import pytest
import allure
from unittest.mock import MagicMock, patch, call

# Import the module under test
import useful_tools.front as front

# --- Fixtures ---

@pytest.fixture
def mock_pil_image():
    """Mocks PIL.Image methods like open, new."""
    with patch('front.Image') as mock_img_cls:
        # Mock the image object returned by open() or new()
        mock_img_instance = MagicMock()
        
        # Chainable methods: rotate returns self, resize returns self
        mock_img_instance.rotate.return_value = mock_img_instance
        mock_img_instance.resize.return_value = mock_img_instance
        
        mock_img_cls.open.return_value = mock_img_instance
        mock_img_cls.new.return_value = mock_img_instance
        
        yield mock_img_cls

@pytest.fixture
def mock_pil_draw():
    """Mocks PIL.ImageDraw."""
    with patch('front.ImageDraw.Draw') as mock_draw_constructor:
        mock_draw_instance = MagicMock()
        mock_draw_constructor.return_value = mock_draw_instance
        
        # Mock textbbox to return fixed dimensions (left, top, right, bottom)
        # Width = 100-0 = 100, Height = 20-0 = 20
        mock_draw_instance.textbbox.return_value = (0, 0, 100, 20)
        
        yield mock_draw_instance

@pytest.fixture
def mock_pil_font():
    """Mocks PIL.ImageFont."""
    with patch('front.ImageFont') as mock_font_cls:
        yield mock_font_cls

# --- Tests ---

@allure.epic("Image Generation")
@allure.suite("Graphics Utils")
@allure.feature("Text Positioning")
class TestTextDrawing:

    @allure.story("Calculations")
    @allure.title("Calculate centered position correctly")
    def test_draw_centered_text(self, mock_pil_draw):
        """
        Scenario: Text bounding box is 100x20. Center is (500, 500).
        Expectation: Top-left x = 500 - (100/2) = 450.
                     Top-left y = 500 - (20/2) = 490.
        """
        mock_draw = mock_pil_draw
        mock_font = MagicMock()
        
        front.draw_centered_multiline_text(
            draw=mock_draw,
            text="Hello",
            center_x=500,
            center_y=500,
            font=mock_font
        )
        
        # Verify textbbox was called to measure size
        mock_draw.textbbox.assert_called()
        
        # Verify multiline_text was called with calculated coordinates
        args, kwargs = mock_draw.multiline_text.call_args
        
        # args[0] is the (x, y) tuple
        x, y = args[0]
        assert x == 450.0
        assert y == 490.0
        assert args[1] == "Hello"


@allure.epic("Image Generation")
@allure.suite("A5 Layout")
@allure.feature("Canvas Assembly")
class TestA5Creation:

    @allure.story("Image Processing")
    @allure.title("Open, rotate, resize, and paste inputs")
    def test_image_manipulation(self, mock_pil_image, mock_pil_draw, mock_pil_font):
        """
        Scenario: Two image paths provided.
        Expectation: Both opened, rotated 180, resized, and pasted onto canvas.
        """
        front.create_a5_png_with_line_and_centered_text(
            img_path_top="top.jpg",
            img_path_bottom="bot.jpg",
            output_path="out.png"
        )
        
        # 1. Verify Canvas Creation (A5 Size)
        mock_pil_image.new.assert_called_with("RGB", (1748, 2480), "white")
        
        # 2. Verify Inputs Opened
        mock_pil_image.open.assert_has_calls([call("top.jpg"), call("bot.jpg")], any_order=True)
        
        # 3. Verify Transforms (Rotate -> Resize)
        # We check the mock instance returned by open()
        img_instance = mock_pil_image.open.return_value
        assert img_instance.rotate.call_count == 2
        img_instance.rotate.assert_called_with(180, expand=True)
        
        assert img_instance.resize.call_count == 2
        # Resize dimensions should be A5 Width x Calculated Height
        # Height = (2480 // 2) - 200 = 1040
        img_instance.resize.assert_called_with((1748, 1040), ANY)
        
        # 4. Verify Pasting onto Canvas
        canvas = mock_pil_image.new.return_value
        assert canvas.paste.call_count == 2
        
    @allure.story("Drawing")
    @allure.title("Draw middle divider line")
    def test_divider_line(self, mock_pil_image, mock_pil_draw, mock_pil_font):
        front.create_a5_png_with_line_and_centered_text("a.jpg", "b.jpg")
        
        # Middle Y is 2480 // 2 = 1240
        expected_coords = (0, 1240, 1748, 1240)
        
        mock_pil_draw.line.assert_called_with(expected_coords, fill="black", width=3)

    @allure.story("Fonts")
    @allure.title("Fallback to default font on OSError")
    def test_font_fallback(self, mock_pil_image, mock_pil_draw, mock_pil_font):
        """
        Scenario: Truetype font file is missing (OSError).
        Expectation: Fallback to ImageFont.load_default().
        """
        # Simulate missing font file
        mock_pil_font.truetype.side_effect = OSError("Font not found")
        
        front.create_a5_png_with_line_and_centered_text("a.jpg", "b.jpg")
        
        # Should call load_default twice (top and bottom font)
        assert mock_pil_font.load_default.call_count == 2

    @allure.story("File Output")
    @allure.title("Save final canvas to disk")
    def test_save_output(self, mock_pil_image, mock_pil_draw, mock_pil_font):
        front.create_a5_png_with_line_and_centered_text("a.jpg", "b.jpg", output_path="final.png")
        
        canvas = mock_pil_image.new.return_value
        canvas.save.assert_called_once_with("final.png")

# Helper for wildcard assertions if needed (e.g. Image.LANCZOS)
from unittest.mock import ANY