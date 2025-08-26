import os
import shutil
import uuid
from typing import List

from PIL import Image


MEDIA_DIR = os.path.join(os.path.dirname(__file__), "data", "media")


def ensure_media_dir() -> None:
    os.makedirs(MEDIA_DIR, exist_ok=True)


def save_uploaded_images(images: List[Image.Image]) -> List[str]:
    ensure_media_dir()
    saved_paths: List[str] = []
    for img in images:
        filename = f"{uuid.uuid4().hex}.png"
        path = os.path.join(MEDIA_DIR, filename)
        img.save(path, format="PNG")
        saved_paths.append(path)
    return saved_paths


def delete_media(paths: List[str]) -> None:
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            # Best-effort cleanup
            pass


