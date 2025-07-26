import json

def evaluate_text(text):
    # Dummy logic: Count words and characters
    result = {
        "word_count": len(text.split()),
        "character_count": len(text),
        "summary": text[:100] + "..." if len(text) > 100 else text
    }
    return result

def save_to_json(result, filename="output.json"):
    with open(filename, "w") as f:
        json.dump(result, f, indent=4)

# # Example usage
# if __name__ == "__main__":
#     # Sample input, later this will come from other modules
#     sample_text = "This is a sample document used for testing the logic evaluator's capability."
#     result = evaluate_text(sample_text)
#     save_to_json(result)
#     print("Evaluation complete. Output saved to output.json.")
