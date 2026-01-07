import numpy as np
import json
from typing import List

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            self.model = None
        else:
            self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]):
        if self.model is None:
            # fallback: simple hash-based vectors (for dev only)
            return [self._mock_vector(t) for t in texts]
        arr = self.model.encode(texts)
        return arr.tolist()

    def _mock_vector(self, text: str):
        h = abs(hash(text)) % (10 ** 6)
        rng = np.random.RandomState(h)
        return rng.rand(384).tolist()
