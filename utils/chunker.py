import tiktoken

def tokenize_and_chunk(text: str, max_tokens: int = 300, overlap: int = 100):
    enc = tiktoken.get_encoding("cl100k_base")  # Gemini/BERT-compatible tokenizer
    tokens = enc.encode(text)

    chunks = []
    seen = set()
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)

        # Deduplicate in case overlap creates same chunks
        if chunk_text.strip() not in seen:
            chunks.append(chunk_text.strip())
            seen.add(chunk_text.strip())

        start += max_tokens - overlap  # move window forward with overlap
    return chunks
