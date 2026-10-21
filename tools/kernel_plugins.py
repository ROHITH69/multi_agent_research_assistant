"""Semantic Kernel plugins exposing the project's deterministic Python tools."""
from semantic_kernel.functions import kernel_function
from agents.planner_agent import extract_keywords, generate_subquestions
from tools.document_tools import search_documents, retrieve_passages
from tools.analysis_tools import group_findings_by_theme, compare_evidence
from tools.review_tools import verify_citations, detect_unsupported_claims
from tools.writer_tools import validate_report_sources

class PlannerToolsPlugin:
    @kernel_function(description="Extract research keywords from a question.")
    def extract_keywords(self, question: str) -> str:
        return ", ".join(extract_keywords(question))

    @kernel_function(description="Generate research subquestions.")
    def generate_subquestions(self, question: str) -> str:
        return " | ".join(generate_subquestions(question, extract_keywords(question)))

class ResearchToolsPlugin:
    @kernel_function(description="Search the local research corpus.")
    def search_documents(self, query: str) -> str:
        import json
        return json.dumps(search_documents(query), ensure_ascii=False)

    @kernel_function(description="Retrieve relevant passages from the local research corpus.")
    def retrieve_passages(self, query: str) -> str:
        import json
        return json.dumps(retrieve_passages(query), ensure_ascii=False)

class AnalysisToolsPlugin:
    @kernel_function(description="Group evidence by theme.")
    def group_findings_by_theme(self, evidence_json: str) -> str:
        import json
        return json.dumps(group_findings_by_theme(json.loads(evidence_json)), ensure_ascii=False)

    @kernel_function(description="Compare evidence and return heuristic observations.")
    def compare_evidence(self, evidence_json: str) -> str:
        import json
        return json.dumps(compare_evidence(json.loads(evidence_json)), ensure_ascii=False)

class ReviewToolsPlugin:
    @kernel_function(description="Verify source identifiers in a report.")
    def verify_citations(self, report: str, valid_source_ids_json: str) -> str:
        import json
        return json.dumps(verify_citations(report, set(json.loads(valid_source_ids_json))))

    @kernel_function(description="Detect claims whose sources are absent from retrieved evidence.")
    def detect_unsupported_claims(self, analysis_json: str, evidence_json: str) -> str:
        import json
        return json.dumps(detect_unsupported_claims(json.loads(analysis_json), json.loads(evidence_json)))

class WriterToolsPlugin:
    @kernel_function(description="Validate report source references.")
    def validate_report_sources(self, report: str, evidence_json: str) -> str:
        import json
        return str(validate_report_sources(report, json.loads(evidence_json))).lower()
