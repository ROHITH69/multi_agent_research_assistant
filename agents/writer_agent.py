from __future__ import annotations
from tools.writer_tools import format_research_report, validate_report_sources

class WriterAgent:
    name = "writer_agent"
    def run(self, question: str, analysis: dict, evidence: list[dict]) -> str:
        report = format_research_report(
            question, analysis.get("themes", {}), analysis.get("claims", []),
            evidence, analysis.get("limitations", []), analysis.get("dropped_claims", [])
        )
        # Tool 2: validate source references before returning the artifact.
        if not validate_report_sources(report, evidence):
            raise ValueError("Writer generated a report with source IDs absent from retrieved evidence.")
        return report

    def validate(self, report: str, evidence: list[dict]) -> bool:
        return validate_report_sources(report, evidence)
