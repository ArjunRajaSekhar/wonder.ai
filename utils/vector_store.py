# utils/vector_store.py
from __future__ import annotations
import os, json, uuid
from typing import List, Dict, Any, Optional
import numpy as np
import faiss

from utils.embeddings import Embeddings

class ProjectVectorStore:
    """Simple FAISS (cosine) store per project, persisted to disk.
    Files:
      - index.faiss (FAISS index)
      - meta.jsonl (one JSON per vector: {id, text, metadata})
    """
    def __init__(self, project_dir: str):
        os.makedirs(project_dir, exist_ok=True)
        self.project_dir = project_dir
        self.index_path = os.path.join(project_dir, "index.faiss")
        self.meta_path  = os.path.join(project_dir, "meta.jsonl")
        self._dim = None
        self.index = None
        self._load()

    def _load(self):
        if os.path.exists(self.meta_path):
            # Peek a line to infer dim via embedding later only when needed
            pass
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)

    def _ensure_index(self, dim: int):
        if self.index is None:
            # Cosine sim = inner product on L2-normalized vectors
            self.index = faiss.IndexFlatIP(dim)

    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        if not texts:
            return []
        embs = Embeddings.embed(texts)
        self._ensure_index(embs.shape[1])
        self.index.add(embs.astype(np.float32))
        ids = []
        with open(self.meta_path, "a", encoding="utf-8") as f:
            for i, text in enumerate(texts):
                doc_id = uuid.uuid4().hex[:12]
                ids.append(doc_id)
                meta = (metadatas[i] if metadatas and i < len(metadatas) else {})
                rec = { "id": doc_id, "text": text, "metadata": meta }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        faiss.write_index(self.index, self.index_path)
        return ids

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if self.index is None:
            return []
        q = Embeddings.embed([query]).astype(np.float32)
        D, I = self.index.search(q, min(k, self.index.ntotal))
        # Retrieve rows from meta.jsonl by position order
        # We'll stream the file and collect in order
        hits = []
        pos_map = {int(idx): score for idx, score in zip(I[0], D[0]) if idx >= 0}
        if not pos_map:
            return []
        # Read all rows and pick those positions
        rows = []
        with open(self.meta_path, "r", encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line))
        for i, rec in enumerate(rows):
            if i in pos_map:
                rec_out = dict(rec)
                rec_out["score"] = float(pos_map[i])
                hits.append(rec_out)
        # Sort by score desc
        hits.sort(key=lambda r: r.get("score", 0.0), reverse=True)
        return hits

    @staticmethod
    def for_project(project_id: str) -> "ProjectVectorStore":
        base = os.environ.get("VECTOR_BASE", "./vectorstores")
        project_dir = os.path.join(base, project_id)
        return ProjectVectorStore(project_dir)

    # Convenience to store generated code artifacts
    def index_code_artifacts(self, code: Dict[str, str], extra_meta: Optional[Dict[str, Any]] = None):
        texts = []
        metas = []
        for k in ("html", "css", "js"):
            if not code or not code.get(k):
                continue
            texts.append(code[k])
            meta = {"type": "code", "lang": k.upper()}
            if extra_meta:
                meta.update(extra_meta)
            metas.append(meta)
        if texts:
            self.add_texts(texts, metas)
