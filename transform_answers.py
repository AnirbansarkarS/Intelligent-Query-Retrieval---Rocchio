import json

def transform_answers(input_path="qa_results_optimized.json", output_path="answers.json"):
    with open(input_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    answers_list = []

    for i, item in enumerate(data):
        try:
            # Case 1: already a dict with 'answer' key
            if isinstance(item, dict) and "answer" in item:
                answer_entry = item["answer"]
                
                # Case: answer field is a JSON string
                if isinstance(answer_entry, str):
                    try:
                        parsed = json.loads(answer_entry)
                        answers_list.append(parsed["answer"])
                    except:
                        # fallback: treat the string as plain answer
                        answers_list.append(answer_entry.strip())
                else:
                    answers_list.append(answer_entry)

            # Case 2: if item itself is a stringified dict
            elif isinstance(item, str):
                try:
                    parsed_item = json.loads(item)
                    if "answer" in parsed_item:
                        answers_list.append(parsed_item["answer"])
                except:
                    continue  # skip badly malformed strings
        except:
            continue

    output = {"answers": answers_list}

    with open(output_path, "w", encoding="utf-8") as out_file:
        json.dump(output, out_file, indent=4, ensure_ascii=False)

    print(f"✅ Extracted {len(answers_list)} answers into '{output_path}'.")

# Call the function
transform_answers()
