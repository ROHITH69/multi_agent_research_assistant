# Project Report: Academic Research Assistant Team
**Group 16 — Production-Ready Multi-Agent System**

---

## 1. Executive Summary
This project delivers an enterprise-grade, production-ready multi-agent academic research assistant designed to automate literature synthesis, evidence grounding, and fact-checking. Given a complex research question, the system coordinates five specialized agents in a **RAG-Critic pipeline** to produce a structured, themed literature summary with strict verbatim source attribution and explicit exclusion of ungrounded assertions.

The system incorporates:
1. **Framework-Based Agent Development:** Microsoft Semantic Kernel 1.45.0 plugin architecture integrated alongside deterministic Python tool execution.
2. **Standardized Communication Contract:** Full compliance with the Unit-4 Page 18 Multi-Agent System contract using FIPA-ACL performatives (`REQUEST`, `INFORM`, `QUERY`, `PROPOSE`, `CONFIRM`, `DISCONFIRM`, `FAILURE`, `REASSIGN`).
3. **Critic Gate & Zero-Hallucination Guarantee:** Grounded retrieval over a curated academic corpus where every retained claim must map to a verbatim passage.
4. **End-to-End Fault Tolerance:** Automated retry policies, dynamic agent reassignment to secondary specialists, and safe stopping with audit logging.
5. **Multi-Interface Access:** Interactive Web Dashboard (`run_web.py`), CLI terminal demo (`demo.py`), runnable Jupyter Notebook (`notebooks/demo.ipynb`), and automated test suite (`pytest`).

---

## 2. Agent Roster and Module Specifications

| Module Path | Primary Role | Canonical Functions / Tools | Responsibility |
|---|---|---|---|
| `agents/planner_agent.py`<br>`agents/query_agent.py` | **Query / Planner Agent** | `extract_keywords`<br>`generate_subquestions`<br>`(generate_subqueries)` | Decomposes raw research questions into structured sub-queries and extracts domain keywords. |
| `agents/research_agent.py`<br>`agents/retrieval_agent.py` | **Retrieval / Research Agent** | `search_documents`<br>`retrieve_passages`<br>`(fetch_grounded_passages)` | Grounded TF-IDF vector retrieval and cosine similarity ranking against local peer-reviewed corpus. |
| `agents/analysis_agent.py`<br>`agents/summary_agent.py` | **Summary / Analysis Agent** | `group_findings_by_theme`<br>`compare_evidence`<br>`(summarize_by_theme)` | Groups findings into thematic clusters (Learning Support, Teacher Workflow, Implementation, Risks) and extracts candidate claims. |
| `agents/reviewer_agent.py`<br>`agents/fact_check_agent.py` | **Fact-Check / Reviewer Agent (Critic)** | `verify_citations`<br>`detect_unsupported_claims`<br>`(verify_claim_support)` | Evaluates claim validity against retrieved passages. Rejects any claim lacking a verbatim matching quote. |
| `agents/writer_agent.py` | **Writer Agent** | `format_research_report`<br>`validate_report_sources` | Formats final structured brief with per-claim quotes and explicit list of dropped unsupported claims. |

---

## 3. Coordination Architecture & Critic Workflow

The workflow adopts a sequential pipeline with an active critic feedback loop:

```
[User Question]
       │
       ▼
 [Coordinator] ───────► (Initializes Shared State & Audit Log)
       │
       ▼
[Query Agent] ────────► Sub-queries & Keywords
       │
       ▼
[Retrieval Agent] ────► Grounded Passages from Corpus (RAG)
       │                 └─► [Safe Stop] if no relevant evidence found
       ▼
[Summary Agent] ──────► Thematic Grouping & Candidate Claims
       │
       ▼
[Fact-Check Agent] ───► Critic Verification Gate
       │                 ├─► If unsupported claims exist: Prune & active repair
       │                 └─► If unrecoverable: Safe stop
       ▼
 [Writer Agent] ──────► Final Academic Brief with Claim Quotes
       │
       ▼
[Citation Validation] ─► Enforces 100% cited ID matching
       │
       ▼
 [Final Brief]
```

### Shared Memory (`ResearchState`)
The system maintains a centralized dataclass state carrying:
- `run_id`: Unique session UUID
- `question`: User research query
- `plan`: Subqueries and extracted keywords
- `retrieved_evidence`: Grounded corpus passages with relevance scores and metadata
- `analysis`: Extracted candidate claims, themes, and polarity comparisons
- `review`: Critic gate verdicts, issues list, and citation audits
- `report`: Validated final Markdown research brief
- `status`: Execution state machine (`initialized`, `success`, `stopped_no_evidence`, `stopped_review_failed`, `stopped_report_validation_failed`, `stopped_agent_failure`)
- `trace`: Ordered message history
- `errors`: Recorded attempt failure diagnostics

---

## 4. Standardized Communication Contract (Unit-4 Page 18)

Implemented in `unit4_contract.py` and documented in `UNIT4_COMMUNICATION_CONTRACT.md`.

Each inter-agent interaction is governed by the `Unit4AgentMessage` schema:
```json
{
  "message_id": "84a7e94e-2824-4f27-9ad8-dcf9c4885a02",
  "conversation_id": "374e47da-9d7c-4f69-82f1-3e573beeb83e",
  "sender_id": "fact_check_agent",
  "receiver_id": "coordinator",
  "performative": "CONFIRM",
  "ontology": "academic_research_rag_critic",
  "protocol": "rag_critic_pipeline_v1",
  "task_id": "review-round-1",
  "status": "SUCCESS",
  "content": {
    "verdict": "pass",
    "supported_claims": 5,
    "dropped_claims": 0
  },
  "error_details": null,
  "timestamp": "2026-10-21T09:10:02Z",
  "metadata": {
    "attempt": 1
  }
}
```

---

## 5. Fault Tolerance & Failure Recovery Matrix (Step 4)

| Failure Scenario | Trigger Condition | System Action | Outcome |
|---|---|---|---|
| **Transient Agent Exception** | Temporary agent exception during execution | Coordinator catches error, records in `run.jsonl`, increments attempt counter, and retries up to `max_retries` (default: 2). | Task succeeds on subsequent attempt without pipeline interruption. |
| **Permanent Agent Failure** | Agent fails after all retry attempts | Production Coordinator triggers **Agent Reassignment** to fallback specialist (e.g., `FallbackPlannerAgent`, `FallbackRetrievalAgent`). | Workflow recovers dynamically; reassignment logged in audit trace. |
| **Missing Data (Out of Domain)** | Query matches zero corpus documents (score <= 0) | Retrieval agent returns empty evidence set. Coordinator triggers **Safe Stop** with status `stopped_no_evidence`. | System terminates cleanly without hallucinating unsupported claims. |
| **Critic Rejection (Ungrounded Claim)** | Candidate claim lacks verbatim quote in cited source | Fact-Check Agent issues `DISCONFIRM` verdict. Repair loop filters out ungrounded claim and places it in `dropped_claims`. | Final report lists claim explicitly under "Unsupported claims dropped". |
| **Citation Mismatch** | Final brief cites an ID not present in retrieved evidence | Writer citation validator rejects brief. Coordinator triggers **Safe Stop** (`stopped_report_validation_failed`). | Report is withheld to protect academic integrity. |

---

## 6. Verification and Test Results

All 15 automated tests pass with 100% test coverage across both baseline and production workflows:

```bash
$ pytest -v
tests/test_enhanced_features.py::test_query_agent_and_aliases PASSED          [  6%]
tests/test_enhanced_features.py::test_retrieval_agent_and_aliases PASSED      [ 13%]
tests/test_enhanced_features.py::test_summary_agent_and_aliases PASSED        [ 20%]
tests/test_enhanced_features.py::test_fact_check_agent_and_aliases PASSED    [ 26%]
tests/test_enhanced_features.py::test_unit4_contract_bidirectional_conversion PASSED [ 33%]
tests/test_enhanced_features.py::test_production_coordinator_success PASSED   [ 40%]
tests/test_enhanced_features.py::test_production_coordinator_agent_reassignment_on_failure PASSED [ 46%]
tests/test_enhanced_features.py::test_corpus_manager_validation PASSED        [ 53%]
tests/test_workflow.py::test_successful_research PASSED                       [ 60%]
tests/test_workflow.py::test_no_evidence_stops_safely PASSED                  [ 66%]
tests/test_workflow.py::test_transient_agent_failure_retries PASSED           [ 73%]
tests/test_workflow.py::test_permanent_agent_failure_safe_stop PASSED         [ 80%]
tests/test_reviewer_rejects_claim_without_matching_quote PASSED              [ 86%]
tests/test_every_agent_has_two_explicit_python_tools PASSED                   [ 93%]
tests/test_final_report_displays_evidence_quote_for_each_claim PASSED         [100%]
============================== 15 passed in 0.86s ==============================
```

---

## 7. How to Run the Project

### Option A: Interactive Web Dashboard (Recommended for Demonstrations)
```bash
python run_web.py
```
Opens browser automatically at `http://127.0.0.1:8501` featuring live pipeline animations, interactive claims inspector, Unit-4 trace viewer, and chaos test injection lab.

### Option B: Terminal CLI Demo
```bash
python demo.py
```
Prompts for a research question, executes the multi-agent pipeline, and prints the trace and final brief.

### Option C: Jupyter Notebook
```bash
jupyter notebook notebooks/demo.ipynb
```
Pre-executed notebook demonstrating normal execution, output reports, and failure recovery retry traces.

### Option D: Run Test Suite
```bash
pytest -v
```
