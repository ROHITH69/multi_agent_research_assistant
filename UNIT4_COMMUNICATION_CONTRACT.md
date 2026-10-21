# Unit-4 Multi-Agent System Communication Contract (Page 18)

## 1. Overview
In multi-agent systems (MAS) and collaborative agent architectures, individual agents communicate through a standardized envelope to ensure:
1. **Decoupled Autonomy:** Senders and receivers interact via defined speech acts (performatives) rather than direct function invocation.
2. **End-to-End Traceability:** Every message carries a persistent `conversation_id` and unique `message_id`.
3. **Structured Semantics:** Structured payloads enable rigorous validation, critic evaluation, and fault recovery.

This specification implements the **Unit-4 Page 18 Multi-Agent System Communication Standard**, fully aligning with FIPA-ACL (Agent Communication Language) protocols.

---

## 2. Standardized Message Fields

| Field | Type | Description | Unit-4 Role |
|---|---|---|---|
| `message_id` | `UUID string` | Unique identifier for each communication instance | Message Deduplication & Logging |
| `conversation_id` | `UUID string` | Persistent ID spanning the complete user research session | Conversation Context & Shared Memory |
| `sender_id` | `string` | Agent role sending the message (e.g., `coordinator`, `query_agent`, `retrieval_agent`) | Identity & Authority Tracking |
| `receiver_id` | `string` | Target agent role receiving the message | Routing & Contract Compliance |
| `performative` | `enum` | Communicative intention/speech act (`REQUEST`, `INFORM`, `QUERY`, `PROPOSE`, `CONFIRM`, `DISCONFIRM`, `FAILURE`, `REASSIGN`) | Speech Act Semantics |
| `ontology` | `string` | Domain vocabulary definition (`"academic_research_rag_critic"`) | Domain Semantics |
| `protocol` | `string` | Interaction pattern (`"rag_critic_pipeline_v1"`) | Coordination Governance |
| `task_id` | `string` | Specific pipeline subtask being executed | Workflow Sequencing |
| `status` | `enum` | Execution status (`SUCCESS`, `FAILED`, `NO_EVIDENCE`, `NEEDS_REVISION`, `REASSIGNED`, `STOPPED`) | State Machine Transition |
| `content` | `dict` | Semantic payload (query keywords, retrieved evidence, claims, reviewer verdict, report) | Shared Payload Transfer |
| `error_details` | `string | null` | Stack trace or failure description if status is not `SUCCESS` | Failure Diagnostics |
| `timestamp` | `ISO-8601 UTC` | Exact creation time of the message | Latency & SLA Auditing |
| `in_reply_to` | `UUID | null` | Reference to previous `message_id` being answered | Causal Trace Ordering |
| `metadata` | `dict` | Execution metadata (attempt count, retry status, fallback flags) | Fault Tolerance Audit |

---

## 3. Performative Taxonomy (Speech Acts)

- `REQUEST`: Coordinator instructs a specialist agent to execute an action.
- `INFORM`: Specialist agent returns its successful computation to the coordinator or downstream agent.
- `QUERY`: Agent requests information retrieval from the corpus or knowledge base.
- `PROPOSE`: Analysis Agent proposes synthesized claims with provisional citations.
- `CONFIRM`: Fact-Check / Critic Agent confirms that claims are grounded in retrieved evidence quotes.
- `DISCONFIRM`: Fact-Check / Critic Agent rejects unsupported claims and flags missing citations.
- `FAILURE`: Agent notifies coordinator of execution failure or unrecoverable error.
- `REASSIGN`: Coordinator notifies the system of dynamic task reassignment to a fallback agent.

---

## 4. Message Flow Sequence

```
User
 │
 ├── (REQUEST) ──> Coordinator
 │                    │
 │                    ├── (REQUEST) ───> Query/Planner Agent
 │                    │                     │
 │                    │ <── (INFORM) ───────┘ (Subquestions & Keywords)
 │                    │
 │                    ├── (REQUEST) ───> Retrieval/Research Agent
 │                    │                     │
 │                    │ <── (INFORM) ───────┘ (Grounded Evidence Passages)
 │                    │
 │                    ├── (REQUEST) ───> Summary/Analysis Agent
 │                    │                     │
 │                    │ <── (PROPOSE) ──────┘ (Themes & Extracted Claims)
 │                    │
 │                    ├── (REQUEST) ───> Fact-Check/Reviewer Agent (Critic Gate)
 │                    │                     │
 │                    │ <── (CONFIRM / ────┘ (Grounding Verification & Dropped Claims)
 │                    │      DISCONFIRM)
 │                    │
 │                    ├── (REQUEST) ───> Writer Agent
 │                    │                     │
 │                    │ <── (INFORM) ───────┘ (Final Validated Research Report)
 │                    │
 └── (INFORM) ────────┘ (Complete Academic Research Brief)
```

---

## 5. JSON Representation Example

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
    "dropped_claims": 0,
    "issues": []
  },
  "error_details": null,
  "timestamp": "2026-10-21T09:10:02.123456Z",
  "in_reply_to": "b93c8371-a7a2-4a0b-99f6-6b216ec78c90",
  "metadata": {
    "attempt": 1,
    "execution_time_ms": 12.4
  }
}
```
