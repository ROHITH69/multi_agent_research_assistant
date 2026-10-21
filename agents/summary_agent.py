from __future__ import annotations
from agents.analysis_agent import AnalysisAgent
from tools.analysis_tools import group_findings_by_theme, compare_evidence

# Functional aliases
summarize_by_theme = group_findings_by_theme
compare_evidence_themes = compare_evidence

class SummaryAgent(AnalysisAgent):
    """Summary Agent: Writes a structured summary grouped by theme from retrieved passages."""
    name = "summary_agent"
