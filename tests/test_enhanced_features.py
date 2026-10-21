from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from coordinator import Coordinator
from production_coordinator import ProductionCoordinator
from agents.query_agent import QueryAgent, extract_search_keywords, generate_subqueries
from agents.retrieval_agent import RetrievalAgent, search_corpus, fetch_grounded_passages
from agents.summary_agent import SummaryAgent, summarize_by_theme, compare_evidence_themes
from agents.fact_check_agent import FactCheckAgent, verify_claim_support, validate_source_citations
from agents.writer_agent import WriterAgent
from unit4_contract import to_unit4_message, from_unit4_message, Unit4AgentMessage
from tools.corpus_manager import CorpusManager

def test_query_agent_and_aliases():
    qa = QueryAgent()
    assert qa.name == "query_agent"
    plan = qa.run("What are benefits and limitations of AI in education?")
    assert "subqueries" in plan
    assert "keywords" in plan
    assert len(plan["subqueries"]) > 0
    assert callable(extract_search_keywords)
    assert callable(generate_subqueries)

def test_retrieval_agent_and_aliases():
    ra = RetrievalAgent()
    assert ra.name == "retrieval_agent"
    evidence = ra.run({"question": "AI in education"})
    assert len(evidence) > 0
    assert callable(search_corpus)
    assert callable(fetch_grounded_passages)

def test_summary_agent_and_aliases():
    sa = SummaryAgent()
    assert sa.name == "summary_agent"
    ra = RetrievalAgent()
    evidence = ra.run({"question": "AI in education"})
    analysis = sa.run(evidence)
    assert "themes" in analysis
    assert "claims" in analysis
    assert callable(summarize_by_theme)
    assert callable(compare_evidence_themes)

def test_fact_check_agent_and_aliases():
    fca = FactCheckAgent()
    assert fca.name == "fact_check_agent"
    ra = RetrievalAgent()
    evidence = ra.run({"question": "AI in education"})
    analysis = SummaryAgent().run(evidence)
    review = fca.run(analysis, evidence)
    assert "verdict" in review
    assert review["verdict"] == "pass"
    assert callable(verify_claim_support)
    assert callable(validate_source_citations)

def test_unit4_contract_bidirectional_conversion():
    from communication import make_message
    msg = make_message(
        run_id="test-run-123",
        sender="query_agent",
        recipient="retrieval_agent",
        task_id="plan",
        message_type="agent_result",
        status="success",
        payload={"query": "AI in education"}
    )
    u4_msg = to_unit4_message(msg)
    assert isinstance(u4_msg, Unit4AgentMessage)
    assert u4_msg.conversation_id == "test-run-123"
    assert u4_msg.sender_id == "query_agent"
    assert u4_msg.receiver_id == "retrieval_agent"
    assert u4_msg.performative == "INFORM"
    assert u4_msg.status == "SUCCESS"

    back_msg = from_unit4_message(u4_msg)
    assert back_msg.run_id == msg.run_id
    assert back_msg.sender == msg.sender
    assert back_msg.recipient == msg.recipient

def test_production_coordinator_success(tmp_path):
    coord = ProductionCoordinator(log_path=tmp_path / "run.jsonl")
    result = coord.run("What are benefits and limitations of AI in education?")
    assert result["status"] == "success"
    assert "elapsed_seconds" in result
    assert "unit4_trace" in result
    assert len(result["unit4_trace"]) > 0
    assert result["report"]

def test_production_coordinator_agent_reassignment_on_failure(tmp_path):
    # Simulate permanent failure of primary planner agent; coordinator should reassign to fallback planner
    def fail_primary_planner(agent_name, attempt):
        return agent_name == "planner_agent"

    coord = ProductionCoordinator(log_path=tmp_path / "run.jsonl", max_retries=1,
                                  failure_injector=fail_primary_planner,
                                  enable_reassignment=True)
    result = coord.run("What are benefits and limitations of AI in education?")
    assert result["status"] == "success"
    assert len(result["reassignments"]) == 1
    assert result["reassignments"][0]["original_agent"] == "planner_agent"
    assert result["reassignments"][0]["reassigned_to"] == "fallback_planner_agent"
    assert result["attempt_counts"]["fallback_planner_agent"] >= 1

def test_corpus_manager_validation():
    cm = CorpusManager()
    val = cm.validate_corpus()
    assert val["all_valid"] is True
    assert val["total_papers"] == 5
    assert "paper_01" in val["source_ids"]
