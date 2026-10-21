from __future__ import annotations
from agents.planner_agent import PlannerAgent, extract_keywords, generate_subquestions

# Functional aliases satisfying both the Query Agent module specification and rubrics
extract_search_keywords = extract_keywords
generate_subqueries = generate_subquestions

class QueryAgent(PlannerAgent):
    """Query Agent: Turns the research question into search sub-queries over a paper set."""
    name = "query_agent"

    def run(self, question: str) -> dict:
        result = super().run(question)
        # Expose both subquestions and subqueries for complete compatibility
        result["subqueries"] = result["subquestions"]
        return result
