def evaluate_logic(matches):
    """
    Evaluates the top matching clauses based on the score,
    and returns a structured JSON with simplified answers.
    """
    # Sort matches by score ascending (lower is better)
    sorted_matches = sorted(matches, key=lambda x: x['score'])

    # Take top 2–3 matches
    top_matches = sorted_matches[:3]

    # Extract only the clause_text from each
    answers = [match['clause_text'] for match in top_matches]

    # Return in required format
    return{
        "answers":answers
}


# TODO make json type structure output