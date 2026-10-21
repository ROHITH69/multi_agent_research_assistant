from __future__ import annotations
from tools.document_tools import search_documents, retrieve_passages

class ResearchAgent:
    name = "research_agent"
    def __init__(self, corpus_dir=None):
        self.corpus_dir = corpus_dir

    def run(self, plan: dict) -> list[dict]:
        question = plan["question"]
        corpus_dir = self.corpus_dir
        # Tool 1: document-level search. Tool 2: passage retrieval for grounding.
        search_documents(question, **({"corpus_dir": corpus_dir} if corpus_dir else {}), top_k=5)
        results = retrieve_passages(question, **({"corpus_dir": corpus_dir} if corpus_dir else {}), top_k=5)
        # Keep one strongest passage per source; never invent fallback evidence.
        unique = {}
        for item in results:
            unique.setdefault(item["source_id"], item)
        return list(unique.values())
