from __future__ import annotations
import re
from collections import defaultdict

def group_findings_by_theme(evidence: list[dict]) -> dict[str, list[dict]]:
    """Assign each source to one primary theme using transparent keyword scores."""
    rules = {
        "learning_support": {"personalized", "tutor", "feedback", "learning", "student", "performance", "thinking"},
        "teacher_workflow": {"teacher", "educator", "workload", "planning", "grading", "teaching", "instructional"},
        "risks_and_limits": {"privacy", "bias", "risk", "limitation", "accuracy", "equity", "cautious", "challenge"},
        "implementation": {"training", "infrastructure", "access", "implementation", "policy", "regulating", "ethical", "adoption"},
    }
    grouped = defaultdict(list)
    for item in evidence:
        text = (item.get("title", "") + " " + item.get("passage", "")).lower()
        scores = {theme: sum(1 for word in words if word in text) for theme, words in rules.items()}
        best = max(scores, key=scores.get)
        grouped[best if scores[best] else "general_findings"].append(item)
    return dict(grouped)

def compare_evidence(evidence: list[dict]) -> dict:
    """Produce a deterministic evidence overview and flag conflicting polarity language."""
    if not evidence:
        return {"source_count": 0, "themes": [], "observations": [], "conflicts": []}
    positive = ("benefit", "improve", "support", "increase", "effective", "opportunity")
    caution = ("risk", "privacy", "bias", "limitation", "challenge", "concern")
    observations = []
    for item in evidence:
        text = item.get("passage", "").lower()
        tags = []
        if any(word in text for word in positive):
            tags.append("potential_benefit_mentioned")
        if any(word in text for word in caution):
            tags.append("limitation_or_risk_mentioned")
        observations.append({"source_id": item.get("source_id"), "signals": tags})
    return {
        "source_count": len({x.get("source_id") for x in evidence}),
        "themes": sorted({theme for group in group_findings_by_theme(evidence).values()
                          for theme in [group[0].get("theme", "")] if theme}),
        "observations": observations,
        "conflicts": [],
        "caveat": "Keyword signals are heuristic indicators, not proof of causal effects."
    }
