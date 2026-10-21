from __future__ import annotations
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CORPUS_DIR = Path(__file__).resolve().parents[1] / "corpus"

def load_documents(corpus_dir: str | Path = CORPUS_DIR) -> list[dict]:
    """Load local JSON documents from the provided corpus directory."""
    docs = []
    for path in sorted(Path(corpus_dir).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        docs.append({**data, "path": str(path)})
    return docs

def search_documents(query: str, corpus_dir: str | Path = CORPUS_DIR, top_k: int = 5) -> list[dict]:
    """Rank corpus documents against a query using TF-IDF cosine similarity."""
    docs = load_documents(corpus_dir)
    if not docs or not query.strip():
        return []
    texts = [d["title"] + " " + d["text"] for d in docs]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts + [query])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    ranked = sorted(zip(scores, docs), key=lambda x: float(x[0]), reverse=True)
    return [{**doc, "score": float(score)} for score, doc in ranked[:top_k] if score > 0]

def retrieve_passages(query: str, corpus_dir: str | Path = CORPUS_DIR, top_k: int = 4) -> list[dict]:
    """Return relevant document text passages with stable source IDs."""
    results = search_documents(query, corpus_dir=corpus_dir, top_k=top_k)
    passages = []
    for item in results:
        # Small local corpus: each document is a passage; truncate only for compact output.
        passages.append({
            "source_id": item["source_id"],
            "title": item["title"],
            "authors": item.get("authors", ""),
            "year": item.get("year", ""),
            "venue": item.get("venue", ""),
            "doi": item.get("doi", ""),
            "url": item.get("url", ""),
            "document_type": item.get("document_type", ""),
            "passage": item["text"],
            "relevance": round(item["score"], 4)
        })
    return passages
