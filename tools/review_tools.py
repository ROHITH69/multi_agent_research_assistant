from __future__ import annotations
import re
import unicodedata


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s'-]", " ", text)).strip()


def verify_citations(report: str, valid_source_ids: set[str]) -> dict:
    """Check bracketed source IDs in a report against known evidence IDs."""
    cited = set(re.findall(r"\[([A-Za-z0-9_-]+)\]", report))
    invalid = sorted(cited - valid_source_ids)
    return {"cited_source_ids": sorted(cited), "invalid_source_ids": invalid,
            "valid": not invalid}


def detect_unsupported_claims(analysis: dict, evidence: list[dict]) -> list[str]:
    """Require each retained claim to quote a passage from its cited retrieved source."""
    by_id = {item.get("source_id"): item.get("passage", "") for item in evidence}
    issues = []
    for claim in analysis.get("claims", []):
        source_id = claim.get("source_id")
        quote = claim.get("evidence_quote", "")
        statement = claim.get("claim", "(unnamed claim)")
        if not source_id or source_id not in by_id:
            issues.append(f"Claim has no retrieved source: {statement}")
            continue
        normalized_passage = _normalize(by_id[source_id])
        normalized_quote = _normalize(quote)
        if not normalized_quote or normalized_quote not in normalized_passage:
            issues.append(f"Claim has no matching evidence quote in {source_id}: {statement}")
    if not evidence:
        issues.append("No evidence was retrieved.")
    return issues
