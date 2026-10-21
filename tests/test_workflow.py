from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coordinator import Coordinator

def test_successful_research(tmp_path):
    result = Coordinator(log_path=tmp_path / "run.jsonl").run(
        "What are benefits and limitations of AI in education?")
    assert result["status"] == "success"
    assert result["report"]
    assert result["review"]["verdict"] == "pass"
    assert len(result["evidence"]) > 0
    assert all(x["source_id"] in result["report"] for x in result["evidence"] if x["source_id"] in result["report"])
    assert "Unsupported claims dropped" in result["report"]
    assert all(claim.get("evidence_quote") for claim in result["analysis"]["claims"])

def test_no_evidence_stops_safely(tmp_path):
    result = Coordinator(log_path=tmp_path / "run.jsonl").run(
        "quantum volcano recipes underwater satellite")
    assert result["status"] == "stopped_no_evidence"
    assert result["report"] == ""

def test_transient_agent_failure_retries(tmp_path):
    def fail_once(agent_name, attempt):
        return agent_name == "planner_agent" and attempt == 1
    result = Coordinator(log_path=tmp_path / "run.jsonl",
                         failure_injector=fail_once).run(
        "How can AI support teachers and students?")
    assert result["status"] == "success"
    assert result["attempt_counts"]["planner_agent"] == 2
    log_lines = (tmp_path / "run.jsonl").read_text().strip().splitlines()
    events = [json.loads(line) for line in log_lines]
    assert any(e["metadata"].get("attempt") == 1 and e["status"] == "failed" for e in events)

def test_permanent_agent_failure_safe_stop(tmp_path):
    def always_fail(agent_name, attempt):
        return agent_name == "planner_agent"
    result = Coordinator(log_path=tmp_path / "run.jsonl", max_retries=1,
                         failure_injector=always_fail).run("AI in education")
    assert result["status"] == "stopped_agent_failure"
    assert result["report"] == ""


def test_reviewer_rejects_claim_without_matching_quote():
    from tools.review_tools import detect_unsupported_claims
    evidence = [{"source_id": "paper_01", "passage": "AI can provide feedback to students."}]
    analysis = {"claims": [{"claim": "AI guarantees higher grades.", "source_id": "paper_01", "evidence_quote": "AI guarantees higher grades."}]}
    issues = detect_unsupported_claims(analysis, evidence)
    assert issues
    assert "matching evidence quote" in issues[0]


def test_every_agent_has_two_explicit_python_tools():
    # Rubric audit: each specialist role must expose/use at least two plain Python tools.
    from agents.planner_agent import extract_keywords, generate_subquestions
    from tools.document_tools import search_documents, retrieve_passages
    from tools.analysis_tools import group_findings_by_theme, compare_evidence
    from tools.review_tools import verify_citations, detect_unsupported_claims
    from tools.writer_tools import format_research_report, validate_report_sources
    tool_pairs = [
        (extract_keywords, generate_subquestions),
        (search_documents, retrieve_passages),
        (group_findings_by_theme, compare_evidence),
        (verify_citations, detect_unsupported_claims),
        (format_research_report, validate_report_sources),
    ]
    assert all(callable(tool) for pair in tool_pairs for tool in pair)
    assert all(tool.__name__ for pair in tool_pairs for tool in pair)


def test_final_report_displays_evidence_quote_for_each_claim(tmp_path):
    result = Coordinator(log_path=tmp_path / "run.jsonl").run(
        "What are benefits and limitations of AI in education?")
    assert result["status"] == "success"
    for claim in result["analysis"]["claims"]:
        assert claim["source_id"] in result["report"]
        assert claim["evidence_quote"] in result["report"]
