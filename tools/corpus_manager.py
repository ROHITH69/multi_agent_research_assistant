from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from tools.document_tools import CORPUS_DIR, load_documents

class CorpusManager:
    """Manages paper corpus verification, metadata integrity, and additions."""
    def __init__(self, corpus_dir: str | Path = CORPUS_DIR):
        self.corpus_dir = Path(corpus_dir)
        self.corpus_dir.mkdir(parents=True, exist_ok=True)

    def list_papers(self) -> list[dict[str, Any]]:
        """List all papers with structured metadata."""
        return load_documents(self.corpus_dir)

    def validate_corpus(self) -> dict[str, Any]:
        """Validate that all papers satisfy required fields for academic citation."""
        papers = self.list_papers()
        required_fields = ["source_id", "title", "text", "authors", "year", "venue"]
        valid_count = 0
        issues = []

        for p in papers:
            missing = [f for f in required_fields if not p.get(f)]
            if missing:
                issues.append(f"Paper {p.get('source_id', 'unknown')} missing: {', '.join(missing)}")
            else:
                valid_count += 1

        return {
            "total_papers": len(papers),
            "valid_papers": valid_count,
            "all_valid": len(issues) == 0 and len(papers) > 0,
            "issues": issues,
            "source_ids": [p["source_id"] for p in papers if "source_id" in p]
        }

    def add_paper(self, source_id: str, title: str, text: str, authors: str,
                  year: int | str, venue: str, doi: str = "", url: str = "",
                  document_type: str = "journal_article") -> Path:
        """Add a new paper record to the corpus directory."""
        paper_data = {
            "source_id": source_id,
            "title": title,
            "authors": authors,
            "year": str(year),
            "venue": venue,
            "doi": doi,
            "url": url,
            "document_type": document_type,
            "text": text.strip()
        }
        file_path = self.corpus_dir / f"{source_id}.json"
        file_path.write_text(json.dumps(paper_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return file_path
