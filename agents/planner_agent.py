from __future__ import annotations
import re

def extract_keywords(question: str) -> list[str]:
    """Extract simple meaningful terms from a research question."""
    stop = {"what", "how", "why", "does", "with", "from", "that", "this", "are", "the", "and", "for", "into"}
    words = re.findall(r"[A-Za-z][A-Za-z-]{2,}", question.lower())
    return list(dict.fromkeys(w for w in words if w not in stop))[:10]

def generate_subquestions(question: str, keywords: list[str]) -> list[str]:
    """Create a repeatable plan for the research question."""
    topic = question.strip().rstrip("?")
    return [
        f"What evidence is available about {topic}?",
        f"What benefits or positive findings are reported about {', '.join(keywords[:3]) or topic}?",
        f"What limitations, risks, or uncertainties are reported about {topic}?",
    ]

class PlannerAgent:
    name = "planner_agent"
    def run(self, question: str) -> dict:
        keywords = extract_keywords(question)
        return {"question": question, "keywords": keywords,
                "subquestions": generate_subquestions(question, keywords)}
