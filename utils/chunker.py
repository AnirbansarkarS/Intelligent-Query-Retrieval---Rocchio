import tiktoken
import re

def split_by_structure(text: str):
    # Example for FAQ/policy type docs
    return re.split(r"\n\s*\n|(?<=\n)- ", text)


def tokenize_and_chunk(text: str, max_tokens: int = 350, overlap: int = 80):
    enc = tiktoken.get_encoding("cl100k_base")
    chunks = []

    for section in split_by_structure(text):
        tokens = enc.encode(section)
        if len(tokens) <= max_tokens:
            chunks.append(section)
        else:
            # Apply sliding window to longer sections
            start = 0
            while start < len(tokens):
                end = min(start + max_tokens, len(tokens))
                chunk = enc.decode(tokens[start:end])
                chunks.append(chunk)
                start += max_tokens - overlap
    return chunks
    
