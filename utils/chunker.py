def chunk_text(text: str, max_words: int = 200, overlap: int = 30):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)
        i += max_words - overlap
    return chunks
