from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4
from pydantic import BaseModel, Field

from communication import AgentMessage, MessageType, Status

# FIPA-compliant performatives as taught in Unit-4 Multi-Agent Systems
Performative = Literal[
    "REQUEST",     # Coordinator requests agent to perform work
    "INFORM",      # Agent responds with computed result/data
    "QUERY",       # Agent queries corpus or external tool
    "PROPOSE",     # Agent proposes draft analysis/hypotheses
    "CONFIRM",     # Critic/Fact-check agent verifies claims as supported
    "DISCONFIRM",  # Critic/Fact-check agent rejects unsupported claims
    "FAILURE",     # Agent execution failed
    "REASSIGN",    # Coordinator reassigns task to backup/fallback agent
]

Unit4Status = Literal[
    "SUCCESS",
    "FAILED",
    "NO_EVIDENCE",
    "NEEDS_REVISION",
    "REASSIGNED",
    "STOPPED",
]

class Unit4AgentMessage(BaseModel):
    """
    Standardized Structured Message Format as defined in:
    Unit-4 Multi-Agent System and Collaboration (Page 18).
    
    This structured envelope provides complete message semantics, protocol governance,
    and traceability across specialized agents in enterprise workflows.
    """
    message_id: str = Field(default_factory=lambda: str(uuid4()), description="Globally unique message identifier")
    conversation_id: str = Field(..., description="Unique workflow or conversation run identifier")
    sender_id: str = Field(..., description="Identifier/role of sending agent")
    receiver_id: str = Field(..., description="Identifier/role of recipient agent")
    performative: Performative = Field(..., description="Speech act / communicative intent (FIPA-ACL standard)")
    ontology: str = Field(default="academic_research_rag_critic", description="Domain knowledge ontology")
    protocol: str = Field(default="rag_critic_pipeline_v1", description="Coordination protocol specification")
    task_id: str = Field(..., description="Identifier of the specific task or step")
    status: Unit4Status = Field(default="SUCCESS", description="Execution status")
    content: dict[str, Any] = Field(default_factory=dict, description="Semantic message payload/body")
    error_details: str | None = Field(default=None, description="Detailed error description if status is FAILED")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO-8601 UTC timestamp")
    in_reply_to: str | None = Field(default=None, description="Message ID of the message being replied to")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Operational metadata (e.g., attempt, latency)")

    # Property accessors for backward compatibility with AgentMessage
    @property
    def run_id(self) -> str:
        return self.conversation_id

    @property
    def sender(self) -> str:
        return self.sender_id

    @property
    def recipient(self) -> str:
        return self.receiver_id

    @property
    def message_type(self) -> str:
        return self.performative.lower()

    @property
    def payload(self) -> dict[str, Any]:
        return self.content

    @property
    def error(self) -> str | None:
        return self.error_details


def map_type_to_performative(message_type: MessageType, status: str) -> Performative:
    """Map generic message_type to standard Unit-4 FIPA speech act."""
    if message_type == "task":
        return "REQUEST"
    if message_type == "error":
        return "FAILURE"
    if message_type == "review":
        return "CONFIRM" if status == "success" else "DISCONFIRM"
    if message_type == "event":
        return "REASSIGN" if status in ("agent_reassigned", "retry_scheduled") else "INFORM"
    return "INFORM"


def map_performative_to_type(performative: Performative) -> MessageType:
    """Map Unit-4 performative back to basic message_type."""
    if performative == "REQUEST":
        return "task"
    if performative == "FAILURE":
        return "error"
    if performative in ("CONFIRM", "DISCONFIRM"):
        return "review"
    if performative == "REASSIGN":
        return "event"
    return "agent_result"


def to_unit4_message(msg: AgentMessage) -> Unit4AgentMessage:
    """Convert an existing AgentMessage instance into a strict Unit-4 AgentMessage."""
    performative = map_type_to_performative(msg.message_type, msg.status)
    status_mapped: Unit4Status = {
        "success": "SUCCESS",
        "failed": "FAILED",
        "no_evidence": "NO_EVIDENCE",
        "needs_revision": "NEEDS_REVISION",
        "stopped": "STOPPED",
    }.get(msg.status, "SUCCESS")

    return Unit4AgentMessage(
        message_id=msg.message_id,
        conversation_id=msg.run_id,
        sender_id=msg.sender,
        receiver_id=msg.recipient,
        performative=performative,
        ontology="academic_research_rag_critic",
        protocol="rag_critic_pipeline_v1",
        task_id=msg.task_id,
        status=status_mapped,
        content=msg.payload,
        error_details=msg.error,
        timestamp=msg.timestamp,
        metadata=msg.metadata or {},
    )


def from_unit4_message(u4_msg: Unit4AgentMessage) -> AgentMessage:
    """Convert a Unit-4 AgentMessage instance into an AgentMessage."""
    msg_type = map_performative_to_type(u4_msg.performative)
    status_mapped: Status = {
        "SUCCESS": "success",
        "FAILED": "failed",
        "NO_EVIDENCE": "no_evidence",
        "NEEDS_REVISION": "needs_revision",
        "STOPPED": "stopped",
        "REASSIGNED": "failed",
    }.get(u4_msg.status, "success")

    return AgentMessage(
        run_id=u4_msg.conversation_id,
        message_id=u4_msg.message_id,
        sender=u4_msg.sender_id,
        recipient=u4_msg.receiver_id,
        task_id=u4_msg.task_id,
        message_type=msg_type,
        status=status_mapped,
        payload=u4_msg.content,
        error=u4_msg.error_details,
        metadata=u4_msg.metadata,
        timestamp=u4_msg.timestamp,
    )
