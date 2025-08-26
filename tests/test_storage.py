import os

from PIL import Image

import storage


def test_generate_and_save_sample_image(tmp_path):
    storage.MEDIA_DIR = str(tmp_path)
    p = storage.save_sample_image(caption="Sample Element")
    assert os.path.exists(p)

    img = Image.open(p)
    assert img.size[0] > 100 and img.size[1] > 100


def test_save_uploaded_images(tmp_path):
    storage.MEDIA_DIR = str(tmp_path)
    img = storage.generate_sample_image()
    paths = storage.save_uploaded_images([img])
    assert len(paths) == 1 and os.path.exists(paths[0])

