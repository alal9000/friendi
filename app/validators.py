from django.core.exceptions import ValidationError
from PIL import Image


def validate_image_size(image):
    min_width, min_height = 150, 150

    # Load the image to check dimensions
    img = Image.open(image)
    width, height = img.size

    if width < min_width or height < min_height:
        raise ValidationError(
            f"Image is too small. Minimum size is {min_width}x{min_height}px."
        )
