from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4
from pydantic import BaseModel, Field

Status = Literal["success", "failed", "no_evidence", "needs_revision", "stopped"]
MessageType = Literal["task", "agent_result", "review", "error", "event"]

class AgentMessage(BaseModel):
    run_id: str
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    sender: str
    recipient: str
    task_id: str
    message_type: MessageType
    status: Status
    payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

def make_message(run_id: str, sender: str, recipient: str, task_id: str,
                 message_type: MessageType, status: Status,
                 payload: dict[str, Any] | None = None, error: str | None = None,
                 attempt: int = 1) -> AgentMessage:
    return AgentMessage(
        run_id=run_id, sender=sender, recipient=recipient, task_id=task_id,
        message_type=message_type, status=status, payload=payload or {},
        error=error, metadata={"attempt": attempt}
    )
