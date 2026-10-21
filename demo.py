from coordinator import Coordinator

if __name__ == "__main__":
    question = input("Research question [What are benefits and limitations of AI in education?]: ").strip()
    if not question:
        question = "What are benefits and limitations of AI in education?"
    result = Coordinator().run(question)
    print("\n=== MULTI-AGENT RUN ===")
    print("Run ID:", result["run_id"])
    print("Status:", result["status"])
    print("Semantic Kernel enabled:", result["semantic_kernel_enabled"])
    print("Sources:", [x["source_id"] for x in result["evidence"]])
    print("\n=== TRACE ===")
    for event in result["trace"]:
        print(f"{event['sender']} -> {event['recipient']} | {event['message_type']} | "
              f"{event['status']} | attempt={event['metadata'].get('attempt', 1)}")
    if result["errors"]:
        print("\nErrors:", *result["errors"], sep="\n- ")
    if result["report"]:
        print("\n=== FINAL REPORT ===\n")
        print(result["report"])
    else:
        print("\nNo report generated. Safe-stop reason:", result["status"])
