import os
from typing import List, Sequence

import numpy as np
from openai import OpenAI
from dotenv import load_dotenv


EMBEDDING_MODEL = "text-embedding-3-small"

# Load environment variables from .env if present
load_dotenv()


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENAI_API_KEY environment variable. Please set it to use embeddings."
        )
    return OpenAI()


def compute_text_embedding(text: str) -> List[float]:
    client = _get_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return list(response.data[0].embedding)


def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    if a.size == 0 or b.size == 0:
        return 0.0
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


