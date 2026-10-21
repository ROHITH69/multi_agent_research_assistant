from __future__ import annotations
from agents.research_agent import ResearchAgent
from tools.document_tools import search_documents, retrieve_passages

# Functional aliases
search_corpus = search_documents
fetch_grounded_passages = retrieve_passages

class RetrievalAgent(ResearchAgent):
    """Retrieval Agent: Fetches relevant passages (RAG) for research queries from corpus."""
    name = "retrieval_agent"
