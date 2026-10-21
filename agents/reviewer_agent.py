from __future__ import annotations
from tools.review_tools import verify_citations, detect_unsupported_claims

class ReviewerAgent:
    name = "reviewer_agent"
    def run(self, analysis: dict, evidence: list[dict]) -> dict:
        # Tool 1: inspect claim/source mappings against retrieved evidence.
        issues = detect_unsupported_claims(analysis, evidence)
        valid_ids = {item.get("source_id") for item in evidence}
        # Tool 2: independently validate all bracketed source IDs in the claim list.
        claim_text = "\n".join(
            f"{claim.get('claim', '')} [{claim.get('source_id', '')}]"
            for claim in analysis.get("claims", [])
        )
        citation_check = verify_citations(claim_text, {x for x in valid_ids if x})
        if not citation_check["valid"]:
            issues.append(f"Invalid source IDs in claims: {citation_check['invalid_source_ids']}")
        return {"verdict": "pass" if not issues and evidence else "fail",
                "issues": issues, "citation_check": citation_check,
                "valid_source_ids": sorted(x for x in valid_ids if x)}
