from typing import List, Dict, Tuple
import faiss
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer


class FAISSIndex:
    def __init__(
        self,
        embed_dim: int,
        index_path: str,
        meta_path: str,
        similarity_threshold: float = 0.5,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.embed_dim = embed_dim
        self.index_path = index_path
        self.meta_path = meta_path
        self.similarity_threshold = similarity_threshold
        self.index = faiss.IndexFlatIP(self.embed_dim)
        self.metadata: List[Dict] = []
        self.model = SentenceTransformer(model_name)
        self.load_index()

    def load_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, encoding="utf-8") as f:
                self.metadata = json.load(f)

    def add_embeddings(self, embeddings: np.ndarray, metadata: List[Dict]):
        self.index.add(embeddings)
        self.metadata.extend(metadata)

    def embed_query(self, query: str) -> np.ndarray:
        vec = self.model.encode([query], normalize_embeddings=True)
        return np.array(vec, dtype=np.float32)

    def search(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        query_vec = self.embed_query(query)
        distances, indices = self.index.search(query_vec, k)
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if score >= self.similarity_threshold:
                results.append((idx, score))
        return results

    def generate_excerpts(self, relevant: List[Tuple[int, float]]) -> List[Tuple[str, Dict]]:
        excerpts = []
        seen_texts = set()
        for rank, (idx, score) in enumerate(relevant, start=1):
            m = self.metadata[idx]
            key = (m.get("source"), m.get("chunk_id"))
            if key not in seen_texts:
                seen_texts.add(key)
                excerpts.append((m["text"], m))
        return excerpts

    def save_index(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
