import os
import json
from pathlib import Path
from typing import List, Dict

import numpy as np
from bs4 import BeautifulSoup
import markdown
import faiss
import tiktoken
from sentence_transformers import SentenceTransformer

# Embedding config
EMBED_DIM = 384  # Embedding size of 'all-MiniLM-L6-v2'
CHUNK_TOKENS = 800
OVERLAP_TOKENS = 200
BATCH_SIZE = 16

# SentenceTransformer setup
model = SentenceTransformer("all-MiniLM-L6-v2")

# FAISS index and metadata
index = faiss.IndexFlatIP(EMBED_DIM)
metadata_store: List[Dict] = []

# Tokenizer setup (for GPT-3.5/4)
tokenizer = tiktoken.get_encoding("cl100k_base")

def tokenize_and_chunk(text: str, chunk_size: int, overlap: int) -> List[str]:
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += chunk_size - overlap
    return chunks

def generate_embedding(text: str) -> List[float]:
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()

def read_text_file(file_path: Path) -> str:
    content = file_path.read_text(encoding="utf-8")
    if file_path.suffix == ".html":
        return BeautifulSoup(content, "html.parser").get_text("\n")
    elif file_path.suffix == ".md":
        html = markdown.markdown(content)
        return BeautifulSoup(html, "html.parser").get_text("\n")
    return content

def resolve_source_url(file_path: Path) -> str:
    parent = file_path.parent.name
    if parent == "course_content":
        return f"https://tds.s-anand.net/#/{file_path.stem}"
    elif parent == "discourse_threads":
        json_path = Path("data/discourse_threads") / f"{file_path.stem}.json"
        if json_path.exists():
            data = json.loads(json_path.read_text(encoding="utf-8"))
            return f"https://discourse.onlinedegree.iitm.ac.in/t/{data['slug']}/{data['id']}"
    elif parent == "output_texts":
        return f"Discourse Thread (cleaned): {file_path.stem}"
    return str(file_path)

def embed_and_index_batch(texts: List[str], metas: List[Dict]):
    vectors = [generate_embedding(text) for text in texts]
    arr = np.array(vectors, dtype=np.float32)
    index.add(arr)
    metadata_store.extend([{"text": t, **m} for t, m in zip(texts, metas)])
    print(f"✅ Indexed {len(texts)} chunks. Total so far: {index.ntotal}")

def process_directory(data_dir: str):
    batch_texts, batch_metas = [], []
    for file_path in Path(data_dir).rglob("*"):
        if file_path.suffix.lower() not in [".txt", ".md", ".html"]:
            continue
        text = read_text_file(file_path)
        print(f"📄 Processing: {file_path} ({len(text.split())} words)")
        chunks = tokenize_and_chunk(text, CHUNK_TOKENS, OVERLAP_TOKENS)
        for i, chunk in enumerate(chunks):
            meta = {"source": resolve_source_url(file_path), "chunk_id": i}
            batch_texts.append(chunk)
            batch_metas.append(meta)
            if len(batch_texts) >= BATCH_SIZE:
                embed_and_index_batch(batch_texts, batch_metas)
                batch_texts, batch_metas = [], []
    if batch_texts:
        embed_and_index_batch(batch_texts, batch_metas)

if __name__ == "__main__":
    INPUT_DIRS = ["data/course_content", "output_texts"]
    OUTPUT_DIR = "app/models/"
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    for dir_path in INPUT_DIRS:
        print(f"\n🔍 Scanning: {dir_path}")
        process_directory(dir_path)

    faiss.write_index(index, str(Path(OUTPUT_DIR) / "virtual_ta_index.faiss"))
    with open(Path(OUTPUT_DIR) / "virtual_ta_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata_store, f, indent=2, ensure_ascii=False)

    print("\n✅ Indexing complete. FAISS and metadata saved in app/models/")
