import numpy as np
from PIL import Image, ImageFont, ImageDraw
import cv2

# Default ASCII character sets
DENSE_CHARS = '@#S%?*+;:,. '
LIGHT_CHARS = '#+=-:. '

class ASCIIRenderer:
    def __init__(self, font_path=None, font_size=18, density=DENSE_CHARS, color_mode=False):
        """
        font_path: Path to a .ttf monospace font (default: DejaVuSansMono)
        font_size: Font size in points
        density: ASCII character set (string)
        color_mode: If True, render colored ASCII art
        """
        self.font_path = font_path or self._get_default_font()
        self.font_size = font_size
        self.density = density
        self.color_mode = color_mode
        self.font = ImageFont.truetype(self.font_path, self.font_size)
        # Measure font metrics using getbbox() (newer Pillow API)
        bbox = self.font.getbbox('A')
        self.char_width = bbox[2] - bbox[0]  # right - left
        self.char_height = bbox[3] - bbox[1]  # bottom - top

    def _get_default_font(self):
        # Use a common monospace font
        import os
        if os.name == 'nt':
            return 'C:/Windows/Fonts/consola.ttf'
        else:
            return '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'

    def frame_to_ascii_image(self, frame, out_width, out_height):
        """
        Convert a BGR frame to a Pillow Image of (out_width, out_height) with ASCII art filling the frame.
        Returns: Pillow Image
        """
        # Calculate grid size based on font metrics
        cols = out_width // self.char_width
        rows = out_height // self.char_height
        if cols == 0 or rows == 0:
            return Image.new('RGB', (out_width, out_height), color='black')

        # Create a grayscale map for character selection
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small_gray = cv2.resize(gray_frame, (cols, rows), interpolation=cv2.INTER_AREA)

        # If in color mode, create a resized color map for color sampling
        small_color = None
        if self.color_mode:
            small_color = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)

        # Create the final output image canvas
        img = Image.new('RGB', (out_width, out_height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Map brightness to ASCII characters and render onto the canvas
        ascii_chars = np.array(list(self.density))
        n_chars = len(ascii_chars)

        for y in range(rows):
            for x in range(cols):
                # Determine which character to use based on brightness
                brightness = small_gray[y, x]
                char_index = int((brightness / 255) * (n_chars - 1))
                char = ascii_chars[char_index]

                # Determine the color for the character
                if self.color_mode and small_color is not None:
                    b, g, r = small_color[y, x]
                    color = (int(r), int(g), int(b))
                else:
                    color = (0, 0, 0)  # Black for grayscale mode

                # Draw the character
                px, py = x * self.char_width, y * self.char_height
                draw.text((px, py), char, font=self.font, fill=color)

        return img

# Example usage:
# renderer = ASCIIRenderer(font_size=14)
# ascii_str, cols, rows = renderer.image_to_ascii(frame, cols=120)
# img = renderer.ascii_to_image(ascii_str, cols, rows) 