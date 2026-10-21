from __future__ import annotations
import re


def format_research_report(question: str, themes: dict, claims: list[dict],
                           evidence: list[dict], limitations: list[str],
                           dropped_claims: list[str] | None = None) -> str:
    """Render a concise report with claim-level citations and explicit rejected claims."""
    lines = ["# Multi-Agent Research Brief", "", f"**Research question:** {question}", "", "## Executive summary"]
    if claims:
        for c in claims:
            lines.append(f"- **Claim:** {c['claim']} [{c['source_id']}]")
            quote = c.get("evidence_quote", "").strip()
            if quote:
                lines.append(f"  - **Retrieved corpus text:** > {quote}")
    else:
        lines.append("Insufficient relevant evidence was retrieved to support a research summary.")
    lines.extend(["", "## Evidence by theme"])
    if themes:
        for theme, items in sorted(themes.items()):
            lines.append(f"### {theme.replace('_', ' ').title()}")
            for item in items:
                # Keep the passage tied to its source, but avoid multiple paragraphs per item.
                passage = item['passage'].strip()
                lines.append(f"- **{item['title']}** ({item['source_id']}): {passage}")
    else:
        lines.append("No themes could be established from the available evidence.")
    lines.extend(["", "## Unsupported claims dropped"])
    if dropped_claims:
        lines.extend([f"- {claim}" for claim in dropped_claims])
    else:
        lines.append("- None. All retained claims passed the source-and-quote checks.")
    lines.extend(["", "## Limitations"])
    lines.extend([f"- {x}" for x in limitations] or ["- The local corpus is small and is not an exhaustive literature review."])
    lines.extend(["", "## Sources"])
    for item in evidence:
        authors = item.get("authors", "")
        year = item.get("year", "")
        venue = item.get("venue", "")
        doi = item.get("doi", "")
        url = item.get("url", "")
        citation = f"- **{item['source_id']} — {item['title']}**"
        if authors or year or venue:
            citation += f". {authors} ({year}). {venue}."
        if doi:
            citation += f" DOI: {doi}."
        if url:
            citation += f" {url}"
        lines.append(citation)
    return "\n".join(lines)


def validate_report_sources(report: str, evidence: list[dict]) -> bool:
    """Ensure every bracketed source reference is present in retrieved evidence."""
    known = {item.get("source_id") for item in evidence}
    cited = set(re.findall(r"\[([A-Za-z0-9_-]+)\]", report))
    return cited.issubset(known)
