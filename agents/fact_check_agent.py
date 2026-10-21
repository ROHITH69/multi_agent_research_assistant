from __future__ import annotations
from agents.reviewer_agent import ReviewerAgent
from tools.review_tools import verify_citations, detect_unsupported_claims

# Functional aliases
verify_claim_support = detect_unsupported_claims
validate_source_citations = verify_citations

class FactCheckAgent(ReviewerAgent):
    """Fact-Check Agent: Verifies each claim in the summary against retrieved passages and flags unsupported ones."""
    name = "fact_check_agent"
