from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ResearchState:
    run_id: str
    question: str
    plan: dict[str, Any] = field(default_factory=dict)
    retrieved_evidence: list[dict[str, Any]] = field(default_factory=list)
    analysis: dict[str, Any] = field(default_factory=dict)
    review: dict[str, Any] = field(default_factory=dict)
    report: str = ""
    status: str = "initialized"
    trace: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    attempt_counts: dict[str, int] = field(default_factory=dict)
