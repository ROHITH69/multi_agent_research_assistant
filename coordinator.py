from __future__ import annotations
import json
import time
from pathlib import Path
from uuid import uuid4
from typing import Callable

from communication import make_message
from shared_state import ResearchState
from agents.planner_agent import PlannerAgent
from agents.research_agent import ResearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.reviewer_agent import ReviewerAgent
from agents.writer_agent import WriterAgent
from tools.review_tools import verify_citations

LOG_PATH = Path(__file__).resolve().parent / "logs" / "run.jsonl"

class AgentExecutionError(RuntimeError):
    pass

class Coordinator:
    """Coordinates the five specialist modules, shared state, retries and append-only trace."""
    def __init__(self, corpus_dir=None, log_path: str | Path = LOG_PATH, max_retries: int = 2,
                 failure_injector: Callable[[str, int], bool] | None = None):
        self.planner = PlannerAgent()
        self.researcher = ResearchAgent(corpus_dir=corpus_dir)
        self.analyst = AnalysisAgent()
        self.reviewer = ReviewerAgent()
        self.writer = WriterAgent()
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self.failure_injector = failure_injector
        self.kernel = self._initialize_semantic_kernel()

    def _initialize_semantic_kernel(self):
        """Initialize Semantic Kernel and register agent tool plugins when installed."""
        try:
            from semantic_kernel import Kernel
            from tools.kernel_plugins import PlannerToolsPlugin, ResearchToolsPlugin, AnalysisToolsPlugin, ReviewToolsPlugin, WriterToolsPlugin
            kernel = Kernel()
            for plugin, name in [
                (PlannerToolsPlugin(), "planner_tools"),
                (ResearchToolsPlugin(), "research_tools"),
                (AnalysisToolsPlugin(), "analysis_tools"),
                (ReviewToolsPlugin(), "review_tools"),
                (WriterToolsPlugin(), "writer_tools"),
            ]:
                kernel.add_plugin(plugin, plugin_name=name)
            return kernel
        except ImportError:
            # The deterministic workflow remains testable; install requirements for the framework-backed demo.
            return None

    def _log(self, state: ResearchState, sender: str, recipient: str, task_id: str,
             message_type: str, status: str, payload=None, error=None, attempt=1):
        msg = make_message(state.run_id, sender, recipient, task_id, message_type, status,
                           payload=payload or {}, error=error, attempt=attempt)
        row = msg.model_dump(mode="json")
        state.trace.append(row)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _execute(self, state: ResearchState, agent_name: str, fn):
        last_error = None
        for attempt in range(1, self.max_retries + 2):
            state.attempt_counts[agent_name] = attempt
            self._log(state, "coordinator", agent_name, agent_name, "task", "success",
                      {"event": "agent_started"}, attempt=attempt)
            try:
                if self.failure_injector and self.failure_injector(agent_name, attempt):
                    raise RuntimeError(f"Injected failure for {agent_name}, attempt {attempt}")
                result = fn()
                return result
            except Exception as exc:
                last_error = str(exc)
                state.errors.append(f"{agent_name} attempt {attempt}: {last_error}")
                self._log(state, agent_name, "coordinator", agent_name, "error", "failed",
                          error=last_error, attempt=attempt)
                if attempt <= self.max_retries:
                    self._log(state, "coordinator", agent_name, agent_name, "event", "success",
                              {"event": "retry_scheduled"}, attempt=attempt)
        raise AgentExecutionError(f"{agent_name} failed after retries: {last_error}")

    def run(self, question: str) -> dict:
        run_id = str(uuid4())
        state = ResearchState(run_id=run_id, question=question)
        try:
            state.plan = self._execute(state, "planner_agent", lambda: self.planner.run(question))
            self._log(state, "planner_agent", "research_agent", "plan", "agent_result", "success", state.plan)

            state.retrieved_evidence = self._execute(
                state, "research_agent", lambda: self.researcher.run(state.plan))
            self._log(state, "research_agent", "analysis_agent", "evidence", "agent_result",
                      "success" if state.retrieved_evidence else "no_evidence",
                      {"evidence_count": len(state.retrieved_evidence),
                       "source_ids": [e["source_id"] for e in state.retrieved_evidence]})
            if not state.retrieved_evidence:
                state.status = "stopped_no_evidence"
                state.review = {"verdict": "fail", "issues": ["No relevant evidence found in the local corpus."]}
                self._log(state, "coordinator", "user", "final", "agent_result", "no_evidence",
                          {"status": state.status, "message": "No relevant evidence found; no report generated."})
                return self._result(state)

            state.analysis = self._execute(
                state, "analysis_agent", lambda: self.analyst.run(state.retrieved_evidence))
            self._log(state, "analysis_agent", "reviewer_agent", "analysis", "agent_result", "success",
                      {"claim_count": len(state.analysis.get("claims", []))})

            # Reviewer loop: one revision attempt after the initial review.
            for review_round in range(1, 3):
                state.review = self._execute(
                    state, "reviewer_agent",
                    lambda: self.reviewer.run(state.analysis, state.retrieved_evidence))
                self._log(state, "reviewer_agent", "coordinator", f"review-{review_round}", "review",
                          "success" if state.review["verdict"] == "pass" else "needs_revision",
                          state.review)
                if state.review["verdict"] == "pass":
                    break
                # Safe repair: keep only claims whose source ID and verbatim quote match retrieved evidence.
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
                return self._result(state)

            state.report = self._execute(
                state, "writer_agent",
                lambda: self.writer.run(question, state.analysis, state.retrieved_evidence))
            source_check = verify_citations(state.report, {x["source_id"] for x in state.retrieved_evidence})
            if not source_check["valid"] or not self.writer.validate(state.report, state.retrieved_evidence):
                state.status = "stopped_report_validation_failed"
                state.errors.append("Final report contains invalid source references.")
                self._log(state, "coordinator", "user", "final", "agent_result", "stopped",
                          {"status": state.status, "citation_check": source_check})
                return self._result(state)
            state.status = "success"
            self._log(state, "writer_agent", "user", "final", "agent_result", "success",
                      {"status": state.status, "report_length": len(state.report)})
            return self._result(state)
        except AgentExecutionError as exc:
            state.status = "stopped_agent_failure"
            state.errors.append(str(exc))
            self._log(state, "coordinator", "user", "final", "error", "stopped",
                      {"status": state.status}, error=str(exc))
            return self._result(state)

    def _result(self, state: ResearchState) -> dict:
        return {
            "run_id": state.run_id, "status": state.status, "question": state.question,
            "plan": state.plan, "evidence": state.retrieved_evidence, "analysis": state.analysis,
            "review": state.review, "report": state.report, "trace": state.trace,
            "errors": state.errors, "attempt_counts": state.attempt_counts,
            "semantic_kernel_enabled": self.kernel is not None
        }
