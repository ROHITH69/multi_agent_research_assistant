from __future__ import annotations
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Ensure root workspace is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from coordinator import Coordinator, LOG_PATH
from production_coordinator import ProductionCoordinator
from tools.corpus_manager import CorpusManager

STATIC_DIR = Path(__file__).resolve().parent / "static"

class MultiAgentAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self._handle_status()
        elif path == "/api/corpus":
            self._handle_corpus()
        elif path == "/api/logs":
            self._handle_logs()
        elif path == "/api/diagram":
            self._handle_diagram()
        else:
            # Serve static files (index.html, style.css, app.js, etc.)
            if path == "/" or not (STATIC_DIR / path.lstrip("/")).exists():
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/run":
            self._handle_run()
        elif path == "/api/simulate-failure":
            self._handle_simulate_failure()
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _handle_status(self):
        try:
            import semantic_kernel
            sk_version = semantic_kernel.__version__
        except Exception:
            sk_version = "Not available"

        self._send_json({
            "project": "Group 16 - Academic Research Assistant Team",
            "status": "ready",
            "semantic_kernel_version": sk_version,
            "architecture": "Sequential Pipeline with RAG and Critic Gate",
            "agent_roster": [
                {"name": "query_agent", "role": "Query / Planner Agent", "module": "agents/query_agent.py"},
                {"name": "retrieval_agent", "role": "Retrieval / Research Agent", "module": "agents/retrieval_agent.py"},
                {"name": "summary_agent", "role": "Summary / Analysis Agent", "module": "agents/summary_agent.py"},
                {"name": "fact_check_agent", "role": "Fact-Check / Reviewer Agent", "module": "agents/fact_check_agent.py"},
                {"name": "writer_agent", "role": "Writer Agent", "module": "agents/writer_agent.py"},
            ],
            "fault_tolerance": ["retries", "agent_reassignment", "safe_stopping"]
        })

    def _handle_corpus(self):
        cm = CorpusManager()
        papers = cm.list_papers()
        val = cm.validate_corpus()
        self._send_json({
            "validation": val,
            "papers": papers
        })

    def _handle_logs(self):
        if not LOG_PATH.exists():
            self._send_json({"logs": []})
            return
        lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
        # Return latest 100 entries
        records = []
        for line in lines[-100:]:
            try:
                records.append(json.loads(line))
            except Exception:
                pass
        self._send_json({"logs": records, "total_count": len(lines)})

    def _handle_diagram(self):
        svg_path = ROOT_DIR / "architecture.svg"
        if svg_path.exists():
            svg_content = svg_path.read_text(encoding="utf-8")
            self._send_json({"svg": svg_content})
        else:
            self._send_json({"error": "architecture.svg not found"}, status=404)

    def _handle_run(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8")
        try:
            req = json.loads(post_data) if post_data else {}
        except Exception:
            self._send_json({"error": "Invalid JSON payload"}, status=400)
            return

        question = req.get("question", "What are benefits and limitations of AI in education?").strip()
        use_production = req.get("production_mode", True)

        try:
            if use_production:
                coordinator = ProductionCoordinator()
            else:
                coordinator = Coordinator()
            result = coordinator.run(question)
            self._send_json(result)
        except Exception as exc:
            self._send_json({"error": str(exc), "status": "failed"}, status=500)

    def _handle_simulate_failure(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8")
        try:
            req = json.loads(post_data) if post_data else {}
        except Exception:
            self._send_json({"error": "Invalid JSON payload"}, status=400)
            return

        scenario = req.get("scenario", "transient_planner")
        question = req.get("question", "How can AI support teachers and students?")

        if scenario == "transient_planner":
            def fail_once(agent_name, attempt):
                return agent_name == "planner_agent" and attempt == 1
            coord = Coordinator(failure_injector=fail_once)
            result = coord.run(question)
            result["simulation_type"] = "Transient Failure -> Successful Retry"
            self._send_json(result)

        elif scenario == "agent_reassignment":
            def fail_permanent_planner(agent_name, attempt):
                return agent_name == "planner_agent"
            coord = ProductionCoordinator(max_retries=1, failure_injector=fail_permanent_planner, enable_reassignment=True)
            result = coord.run(question)
            result["simulation_type"] = "Permanent Planner Failure -> Agent Reassignment"
            self._send_json(result)

        elif scenario == "no_evidence":
            coord = Coordinator()
            result = coord.run("quantum volcano recipes underwater satellite")
            result["simulation_type"] = "No Grounded Evidence -> Safe Stop"
            self._send_json(result)

        else:
            self._send_json({"error": "Unknown scenario"}, status=400)


def run_server(port: int = 8501):
    import socket
    while port < 8600:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
            break
        except OSError:
            port += 1

    server = HTTPServer(("127.0.0.1", port), MultiAgentAPIHandler)
    print(f"\n=======================================================")
    print(f" Academic Research Assistant Team - Web Dashboard")
    print(f" Group 16 Multi-Agent System")
    print(f" Running at: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()

if __name__ == "__main__":
    run_server()
