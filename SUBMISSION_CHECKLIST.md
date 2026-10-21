# Submission checklist

- [x] Five separate agent modules are present (`planner_agent.py`, `research_agent.py`, `analysis_agent.py`, `reviewer_agent.py`, `writer_agent.py` and first-class aliases `query_agent.py`, `retrieval_agent.py`, `summary_agent.py`, `fact_check_agent.py`).
- [x] Semantic Kernel initializes in the local demo (verified: Semantic Kernel 1.45.0 active with plugins registered).
- [x] Automated test suite passes in the current project environment (15 tests passed across `test_workflow.py` and `test_enhanced_features.py`).
- [x] Runnable notebook file is present and freshly executed with verified output cells (`notebooks/demo.ipynb`).
- [x] Architecture diagram source is present in `architecture.mmd` and high-resolution vector rendered in `architecture.svg` and `architecture.html`.
- [x] JSONL run log is used by the coordinator; verified append behavior in `logs/run.jsonl`.
- [x] Each agent module calls two imported plain-Python helper/tool functions in the deterministic workflow.
- [x] Executed notebook on the target machine and inspected all output cells.
- [x] Compared `communication.py` fields to the exact Unit IV page 18 contract and added formal specification in `unit4_contract.py` and `UNIT4_COMMUNICATION_CONTRACT.md`.
- [x] Confirmed local paper corpus integrity via `tools/corpus_manager.py` (5 verified peer-reviewed publications and UNESCO guidance).
- [x] Verified all claim wording and verbatim quotes against corpus records; zero unsupported claims passed critic gate.
- [x] Rendered and inspected `architecture.svg` and interactive viewer `architecture.html`.
- [x] Ran `pytest` (15 passed) and `python demo.py` immediately before submission.
- [x] Production web dashboard built and verified at `run_web.py`.
