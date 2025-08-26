import base64
import io
import os
from typing import List, Optional

from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv


# Load environment variables from .env if present
load_dotenv()


ASSISTANT_SYSTEM_PROMPT = (
    "You are Garden Guide, an expert assistant for home gardeners. "
    "Provide concise, friendly, and practical advice. When images are provided, "
    "describe what you notice (health issues, pests, diseases), likely causes, and concrete next steps. "
    "If uncertain, ask for more details. Focus on sustainable practices."
)


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable.")
    return OpenAI()


def _image_to_base64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def generate_advice(question_text: str, images: Optional[List[Image.Image]] = None) -> str:
    client = _get_client()
    content: List[dict] = []
    if question_text.strip():
        content.append({"type": "text", "text": question_text.strip()})
    images = images or []
    for img in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{_image_to_base64(img)}",
                },
            }
        )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.5,
    )

    return completion.choices[0].message.content or ""


