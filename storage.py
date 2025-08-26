import os
import shutil
import uuid
from typing import List, Optional

from PIL import Image
from PIL import ImageDraw, ImageFont


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


def generate_sample_image(caption: Optional[str] = None, width: int = 1024, height: int = 1024) -> Image.Image:
    """Generate a sample image using OpenAI API if caption is provided, else fallback to local generation."""
    print("This is the caption:", caption)
    if caption:
        try:
            import openai
            # You may need to set your OpenAI API key elsewhere in your app
            response = openai.images.generate(
                model="dall-e-3",
                prompt=caption,
                n=1,
                size=f"{width}x{height}" if width and height else "1024x1024"
            )
            image_url = response.data[0].url
            # Download the image
            import requests
            from io import BytesIO
            img_data = requests.get(image_url).content
            img = Image.open(BytesIO(img_data)).convert("RGB")
            # Resize to requested size if needed
            if img.size != (width, height):
                img = img.resize((width, height))
            return img
        except Exception as e:
            print("Error generating sample image:", e)
            # If OpenAI or download fails, fallback to local generation
            pass

    # Fallback: local sample image with green gradient and optional caption
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        # gradient from dark to light green
        g = int(80 + (y / max(1, height)) * 120)
        draw.line([(0, y), (width, y)], fill=(60, g, 60))

    # Optional caption text
    text = caption or "Garden Element"
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    tw, th = draw.textlength(text, font=font), 14
    draw.rectangle([(10, height - th - 20), (10 + int(tw) + 20, height - 10)], fill=(255, 255, 255))
    draw.text((20, height - th - 18), text, fill=(34, 139, 34), font=font)
    return img


def save_sample_image(caption: Optional[str] = None) -> str:
    """Generate and persist a sample image, returning its path."""
    ensure_media_dir()
    img = generate_sample_image(caption=caption)
    filename = f"{uuid.uuid4().hex}.png"
    path = os.path.join(MEDIA_DIR, filename)
    img.save(path, format="PNG")
    return path


