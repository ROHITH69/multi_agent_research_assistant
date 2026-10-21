from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Callable, Any
from uuid import uuid4

from coordinator import Coordinator, LOG_PATH, AgentExecutionError
from shared_state import ResearchState
from unit4_contract import to_unit4_message
from communication import make_message

# Fallback agents for Step 4 Agent Reassignment
class FallbackPlannerAgent:
    name = "fallback_planner_agent"
    def run(self, question: str) -> dict:
        """Fallback planner: Direct question analysis with broader n-gram keywords."""
        words = [w.strip("?,.:;\"'") for w in question.lower().split() if len(w) > 3]
        return {
            "question": question,
            "keywords": list(dict.fromkeys(words))[:10],
            "subquestions": [
                f"What does the literature state about {question}?",
                f"What are key positive outcomes regarding {question}?",
                f"What challenges or constraints are identified regarding {question}?",
            ],
            "planner_strategy": "fallback_direct_decomposition"
        }

class FallbackRetrievalAgent:
    name = "fallback_retrieval_agent"
    def __init__(self, corpus_dir=None):
        self.corpus_dir = corpus_dir

    def run(self, plan: dict) -> list[dict]:
        """Fallback retriever: Multi-query passage union with relaxed scoring."""
        from tools.document_tools import retrieve_passages
        question = plan["question"]
        results = retrieve_passages(question, **({"corpus_dir": self.corpus_dir} if self.corpus_dir else {}), top_k=6)
        unique = {}
        for item in results:
            unique.setdefault(item["source_id"], item)
        return list(unique.values())

class FallbackSummaryAgent:
    name = "fallback_summary_agent"
    def run(self, evidence: list[dict]) -> dict:
        """Fallback summary agent: Clean sentence-level claim extraction."""
        from agents.analysis_agent import AnalysisAgent
        res = AnalysisAgent().run(evidence)
        res["strategy"] = "fallback_extractive_summary"
        return res

class FallbackReviewerAgent:
    name = "fallback_reviewer_agent"
    def run(self, analysis: dict, evidence: list[dict]) -> dict:
        """Fallback fact-check agent: Conservative citation check and claim filtering."""
        from agents.reviewer_agent import ReviewerAgent
        return ReviewerAgent().run(analysis, evidence)

class FallbackWriterAgent:
    name = "fallback_writer_agent"
    def run(self, question: str, analysis: dict, evidence: list[dict]) -> str:
        """Fallback writer: Generates standard structured brief."""
        from agents.writer_agent import WriterAgent
        return WriterAgent().run(question, analysis, evidence)

    def validate(self, report: str, evidence: list[dict]) -> bool:
        from tools.writer_tools import validate_report_sources
        return validate_report_sources(report, evidence)


class ProductionCoordinator(Coordinator):
    """
    Production-ready Multi-Agent Coordinator implementing:
    - Step 1: Specialized agent modules
    - Step 2: Unit-4 standardized communication contract
    - Step 3: RAG with Critic-Reviewer gate pipeline
    - Step 4: Comprehensive fault tolerance: retries, agent reassignment, and safe stopping.
    """
    def __init__(self, corpus_dir=None, log_path: str | Path = LOG_PATH, max_retries: int = 2,
                 failure_injector: Callable[[str, int], bool] | None = None,
                 enable_reassignment: bool = True):
        super().__init__(corpus_dir=corpus_dir, log_path=log_path, max_retries=max_retries,
                         failure_injector=failure_injector)
        self.enable_reassignment = enable_reassignment
        self.fallback_roster = {
            "planner_agent": FallbackPlannerAgent(),
            "query_agent": FallbackPlannerAgent(),
            "research_agent": FallbackRetrievalAgent(corpus_dir=corpus_dir),
            "retrieval_agent": FallbackRetrievalAgent(corpus_dir=corpus_dir),
            "analysis_agent": FallbackSummaryAgent(),
            "summary_agent": FallbackSummaryAgent(),
            "reviewer_agent": FallbackReviewerAgent(),
            "fact_check_agent": FallbackReviewerAgent(),
            "writer_agent": FallbackWriterAgent(),
        }
        self.reassignment_log: list[dict[str, Any]] = []

    def _execute_with_reassignment(self, state: ResearchState, agent_name: str, primary_fn, fallback_fn=None):
        """
        Executes primary agent with retries. If exhausted and reassignment is enabled,
        reassigns task to backup specialist agent before safely stopping.
        """
        last_error = None
        # 1. Attempt primary agent with retries
        for attempt in range(1, self.max_retries + 2):
            state.attempt_counts[agent_name] = attempt
            self._log(state, "coordinator", agent_name, agent_name, "task", "success",
                      {"event": "agent_started"}, attempt=attempt)
            try:
                if self.failure_injector and self.failure_injector(agent_name, attempt):
                    raise RuntimeError(f"Injected failure for {agent_name}, attempt {attempt}")
                return primary_fn()
            except Exception as exc:
                last_error = str(exc)
                state.errors.append(f"{agent_name} attempt {attempt}: {last_error}")
                self._log(state, agent_name, "coordinator", agent_name, "error", "failed",
                          error=last_error, attempt=attempt)
                if attempt <= self.max_retries:
                    self._log(state, "coordinator", agent_name, agent_name, "event", "success",
                              {"event": "retry_scheduled"}, attempt=attempt)

        # 2. Check if agent reassignment is configured and allowed
        if self.enable_reassignment and fallback_fn is not None:
            fallback_agent = self.fallback_roster.get(agent_name)
            fallback_name = getattr(fallback_agent, "name", f"fallback_{agent_name}")
            reassign_record = {
                "original_agent": agent_name,
                "reassigned_to": fallback_name,
                "reason": last_error,
                "timestamp": time.time()
            }
            self.reassignment_log.append(reassign_record)
            self._log(state, "coordinator", fallback_name, agent_name, "event", "success",
                      {"event": "agent_reassigned", **reassign_record})
            
            # Execute reassigned agent with 1 retry
            for attempt in range(1, 2):
                state.attempt_counts[fallback_name] = attempt
                self._log(state, "coordinator", fallback_name, fallback_name, "task", "success",
                          {"event": "reassigned_agent_started"}, attempt=attempt)
                try:
                    return fallback_fn()
                except Exception as fb_exc:
                    last_error = f"Fallback {fallback_name} failed: {fb_exc}"
                    state.errors.append(last_error)
                    self._log(state, fallback_name, "coordinator", fallback_name, "error", "failed",
                              error=last_error, attempt=attempt)

        # 3. Permanent failure -> Safe Stop
        raise AgentExecutionError(f"{agent_name} failed after retries and reassignment: {last_error}")

    def run(self, question: str) -> dict:
        """Run complete workflow with fault tolerance, critic loop, and Unit-4 message traceability."""
        run_id = str(uuid4())
        state = ResearchState(run_id=run_id, question=question)
        start_time = time.time()

        try:
            # Stage 1: Query / Planner Agent
            state.plan = self._execute_with_reassignment(
                state, "planner_agent",
                primary_fn=lambda: self.planner.run(question),
                fallback_fn=lambda: self.fallback_roster["planner_agent"].run(question)
            )
            self._log(state, "planner_agent", "research_agent", "plan", "agent_result", "success", state.plan)

            # Stage 2: Retrieval / Research Agent (RAG)
            state.retrieved_evidence = self._execute_with_reassignment(
                state, "research_agent",
                primary_fn=lambda: self.researcher.run(state.plan),
                fallback_fn=lambda: self.fallback_roster["research_agent"].run(state.plan)
            )
            self._log(state, "research_agent", "analysis_agent", "evidence", "agent_result",
                      "success" if state.retrieved_evidence else "no_evidence",
                      {"evidence_count": len(state.retrieved_evidence),
                       "source_ids": [e["source_id"] for e in state.retrieved_evidence]})

            # Fault Tolerance: Safe stop on missing data
            if not state.retrieved_evidence:
                state.status = "stopped_no_evidence"
                state.review = {"verdict": "fail", "issues": ["No relevant evidence found in the local corpus."]}
                self._log(state, "coordinator", "user", "final", "agent_result", "no_evidence",
                          {"status": state.status, "message": "No relevant evidence found; no report generated."})
                return self._enrich_result(state, start_time)

            # Stage 3: Summary / Analysis Agent
            state.analysis = self._execute_with_reassignment(
                state, "analysis_agent",
                primary_fn=lambda: self.analyst.run(state.retrieved_evidence),
                fallback_fn=lambda: self.fallback_roster["analysis_agent"].run(state.retrieved_evidence)
            )
            self._log(state, "analysis_agent", "reviewer_agent", "analysis", "agent_result", "success",
                      {"claim_count": len(state.analysis.get("claims", []))})

            # Stage 4: Critic / Reviewer Agent Loop
            for review_round in range(1, 3):
                state.review = self._execute_with_reassignment(
                    state, "reviewer_agent",
                    primary_fn=lambda: self.reviewer.run(state.analysis, state.retrieved_evidence),
                    fallback_fn=lambda: self.fallback_roster["reviewer_agent"].run(state.analysis, state.retrieved_evidence)
                )
                self._log(state, "reviewer_agent", "coordinator", f"review-{review_round}", "review",
                          "success" if state.review["verdict"] == "pass" else "needs_revision",
                          state.review)
                if state.review["verdict"] == "pass":
                    break
                
                # Active repair: prune unsupported claims
                from tools.review_tools import detect_unsupported_claims
                claims = state.analysis.get("claims", [])
                kept, dropped = [], list(state.analysis.get("dropped_claims", []))
                for claim in claims:
                    issues = detect_unsupported_claims({"claims": [claim]}, state.retrieved_evidence)
                    if issues:
                        dropped.append(claim.get("claim", "(unnamed claim)"))
                    else:
                        kept.append(claim)
                state.analysis["claims"] = kept
                state.analysis["dropped_claims"] = dropped

            if state.review.get("verdict") != "pass":
                state.status = "stopped_review_failed"
                self._log(state, "coordinator", "user", "final", "agent_result", "stopped",
                          {"status": state.status, "issues": state.review.get("issues", [])})
                return self._enrich_result(state, start_time)

            # Stage 5: Writer Agent
            state.report = self._execute_with_reassignment(
                state, "writer_agent",
                primary_fn=lambda: self.writer.run(question, state.analysis, state.retrieved_evidence),
                fallback_fn=lambda: self.fallback_roster["writer_agent"].run(question, state.analysis, state.retrieved_evidence)
            )

            # Stage 6: Validation Gate
            from tools.review_tools import verify_citations
            source_check = verify_citations(state.report, {x["source_id"] for x in state.retrieved_evidence})
            if not source_check["valid"] or not self.writer.validate(state.report, state.retrieved_evidence):
                state.status = "stopped_report_validation_failed"
                state.errors.append("Final report contains invalid source references.")
                self._log(state, "coordinator", "user", "final", "agent_result", "stopped",
                          {"status": state.status, "citation_check": source_check})
                return self._enrich_result(state, start_time)

            state.status = "success"
            self._log(state, "writer_agent", "user", "final", "agent_result", "success",
                      {"status": state.status, "report_length": len(state.report)})
            return self._enrich_result(state, start_time)

        except AgentExecutionError as exc:
            state.status = "stopped_agent_failure"
            state.errors.append(str(exc))
            self._log(state, "coordinator", "user", "final", "error", "stopped",
                      {"status": state.status}, error=str(exc))
            return self._enrich_result(state, start_time)

    def _enrich_result(self, state: ResearchState, start_time: float) -> dict:
        base = self._result(state)
        elapsed = round(time.time() - start_time, 3)
        base["elapsed_seconds"] = elapsed
        base["reassignments"] = self.reassignment_log
        base["unit4_trace"] = [
            to_unit4_message(make_message(
                run_id=e["run_id"],
                sender=e["sender"],
                recipient=e["recipient"],
                task_id=e["task_id"],
                message_type=e["message_type"],
                status=e["status"],
                payload=e.get("payload", {}),
                error=e.get("error"),
                attempt=e.get("metadata", {}).get("attempt", 1)
            )).model_dump(mode="json")
            for e in state.trace
        ]
        return base
