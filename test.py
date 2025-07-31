# ==============================
# Q&A TESTING FOR OPTIMIZED PIPELINE
# ==============================

import json
from core.parser import parse_document
from core.embbeding import run_pipeline  # <-- new optimized version

# ------------------------------
# Document Source
# ------------------------------
doc_url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
context = parse_document(doc_url)  # Must return text string

# ------------------------------
# Questions
# ------------------------------
questions = [
    "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
    "What is the waiting period for pre-existing diseases (PED) to be covered?",
    "Does this policy cover maternity expenses, and what are the conditions?",
    "What is the waiting period for cataract surgery?",
    "Are the medical expenses for an organ donor covered under this policy?",
    "What is the No Claim Discount (NCD) offered in this policy?",
    "Is there a benefit for preventive health check-ups?",
    "How does the policy define a 'Hospital'?",
    "What is the extent of coverage for AYUSH treatments?",
    "Are there any sub-limits on room rent and ICU charges for Plan A?"
]

results = []
print("\n[INFO] Running Q&A tests with optimized pipeline...\n")

# ------------------------------
# Main Execution
# ------------------------------
try:
    # Run full pipeline for all questions
    pipeline_results = run_pipeline(
        doc_id="policy_doc",
        text=context,
        questions=questions,
        meta={"source": "policy.pdf"}
    )

    # Collect answers with details
    for i, res in enumerate(pipeline_results, 1):
        question = res.get("question", "")
        answer = res.get("answer", "").strip()

        qa_entry = {
            "question": question,
            "answer": answer
        }
        results.append(qa_entry)

        # Print for quick verification
        print(f"Q{i}: {question}")
        print(f"A{i}: {answer}")
        print("-" * 80)

except Exception as e:
    print(f"[ERROR] Testing failed: {e}")

# ------------------------------
# Save Results
# ------------------------------
output_file = "qa_results_optimized.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"\n[INFO] Results saved to {output_file}")
