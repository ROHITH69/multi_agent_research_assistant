#!/usr/bin/env python3
"""
Group 16 - Academic Research Assistant Team
Launcher for the interactive Multi-Agent Web Dashboard.
"""
import sys
import webbrowser
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web_app.server import run_server

if __name__ == "__main__":
    port = 8501
    print("\nStarting Group 16 Multi-Agent Research Assistant Dashboard...")
    try:
        # Attempt to open browser automatically
        webbrowser.open_new_tab(f"http://127.0.0.1:{port}")
    except Exception:
        pass
    run_server(port=port)
