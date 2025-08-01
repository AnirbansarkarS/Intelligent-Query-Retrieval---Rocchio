# ==============================
# Q&A TESTING FOR OPTIMIZED PIPELINE
# ==============================

import json
import logging
from core.parser import parse_document
from core.embbeding import run_pipeline  # Updated optimized pipeline

# ------------------------------
# Document Source
# ------------------------------
doc_url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
logging.info(f"[INFO] Parsing document from URL: {doc_url}")
context = parse_document(doc_url)  # Must return plain text string
if not context:
    raise ValueError("Document parsing failed: context is empty.")

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

# ------------------------------
# Main Execution
# ------------------------------
print("\n[INFO] Running Q&A tests with optimized XPOLION pipeline...\n")

results = []

try:
    # Run the optimized retrieval + answer pipeline
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

        # Print each Q&A for verification
        print(f"Q{i}: {question}")
        print(f"A{i}: {answer}")
        print("-" * 80)

except Exception as e:
    logging.error(f"[ERROR] Q&A Testing failed: {e}")

# ------------------------------
# Save Results
# ------------------------------
output_file = "qa_results_optimized.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"\n[INFO] Results saved to {output_file}")
