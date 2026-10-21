from __future__ import annotations
from tools.analysis_tools import group_findings_by_theme, compare_evidence

class AnalysisAgent:
    name = "analysis_agent"
    def run(self, evidence: list[dict]) -> dict:
        themes = group_findings_by_theme(evidence)
        comparison = compare_evidence(evidence)
        claims = []
        for item in evidence:
            passage = item["passage"].strip()
            # Keep a verbatim first sentence as the claim and evidence quote.
            sentence = passage.split(".")[0].strip()
            if sentence:
                quote = sentence + ("." if not sentence.endswith(".") else "")
                claims.append({"claim": quote, "source_id": item["source_id"], "evidence_quote": quote})
        return {"themes": themes, "comparison": comparison, "claims": claims,
                "dropped_claims": [],
                "limitations": [
                    "The corpus contains five concise source records and is not a systematic review.",
                    "Some corpus passages are concise summaries rather than verbatim full-text quotations; verify against the linked publications.",
                    "Automated keyword grouping is heuristic and may miss nuanced context.",
                    "Claims are checked against the local corpus passage and source ID, not independently validated against the full paper."
                ]}
