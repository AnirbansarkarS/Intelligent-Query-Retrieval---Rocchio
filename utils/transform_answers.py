import json

def transform_answers(input_list: list) -> dict:
    answers_list = []

    for item in input_list:
        answer_field = item.get("answer")

        if isinstance(answer_field, str):
            try:
                parsed = json.loads(answer_field)
                answers_list.append(parsed.get("answer", "").strip())
            except json.JSONDecodeError:
                answers_list.append(answer_field.strip())

        elif isinstance(answer_field, dict):
            answers_list.append(answer_field.get("answer", "").strip())

    output = {"answers": answers_list}
    print(f"✅ Extracted {len(answers_list)} answers.")
    return output
