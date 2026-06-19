import pytest
from unittest.mock import Mock
from autogen_core import Image as AGImage
from PIL import Image as PILImage
import os

from simulator_core import extract_images_from_elements

def test_vision_image_extraction():
    # Create a dummy image
    img = PILImage.new('RGB', (10, 10), color='red')
    img_path = "dummy_test_image.png"
    img.save(img_path)

    mock_element = Mock()
    mock_element.mime = "image/png"
    mock_element.path = img_path

    result = extract_images_from_elements([mock_element])

    assert len(result) == 1
    assert isinstance(result[0], AGImage)

    os.remove(img_path)

def test_vision_ignores_non_images():
    mock_element = Mock()
    mock_element.mime = "text/plain"
    mock_element.path = "dummy.txt"

    result = extract_images_from_elements([mock_element])
    assert len(result) == 0
