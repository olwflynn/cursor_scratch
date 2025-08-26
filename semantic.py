from typing import List, Tuple

from embeddings import compute_text_embedding, cosine_similarity
from db import load_all_embeddings


def semantic_search(query: str, top_k: int = 10) -> List[Tuple[int, float]]:
    """Return list of (advice_id, score) sorted by score desc."""
    query_emb = compute_text_embedding(query)
    id_to_emb = load_all_embeddings()
    scored: List[Tuple[int, float]] = []
    for advice_id, emb in id_to_emb:
        score = cosine_similarity(query_emb, emb)
        scored.append((advice_id, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


