import os
from datetime import datetime

def save_image(image, ext='png'):
    """
    Save a Pillow image to the images/ folder with a timestamped filename.
    ext: 'png' or 'jpg'
    Returns the file path.
    """
    if not os.path.exists('images'):
        os.makedirs('images')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'images/ascii_{timestamp}.{ext}'
    image.save(filename)
    return filename 