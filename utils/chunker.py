import tiktoken

def tokenize_and_chunk(text: str, max_tokens: int = 500, overlap: int = 50):
    enc = tiktoken.get_encoding("cl100k_base")  # GPT tokenizer (approx Gemini)
    tokens = enc.encode(text)

    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += max_tokens - overlap  # overlap for context
    return chunks
