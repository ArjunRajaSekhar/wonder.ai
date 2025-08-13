# utils/embeddings.py
import os
from typing import List
import numpy as np

# Prefer sentence-transformers locally for reliability
# (Works offline once the model is cached.)
from sentence_transformers import SentenceTransformer

_DEFAULT_MODEL = os.environ.get("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

class Embeddings:
    _model = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            cls._model = SentenceTransformer(_DEFAULT_MODEL)
        return cls._model

    @classmethod
    def embed(cls, texts: List[str]) -> np.ndarray:
        model = cls._get_model()
        # Normalize embeddings for cosine similarity in FAISS
        embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embs
