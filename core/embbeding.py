# XPOLION - Intelligent Query & Retrieval with Reasoning
# Embedding + Search + Answer Generation

import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
import time
import json

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_KEY"))
EMBED_MODEL = "models/embedding-001"
REASONING_MODEL = "gemini-2.5-flash"

# Configure Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX", "doc-embeddings")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if missing
if INDEX_NAME not in [idx["name"] for idx in pc.list_indexes()]:
    print(f"[INFO] Creating Pinecone index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print("[INFO] Waiting for index to be ready...")
    time.sleep(10)

# Connect to index
index = pc.Index(INDEX_NAME)
print(f"[INFO] Connected to Pinecone index: {INDEX_NAME}")

# Generate embedding
def get_gemini_embedding(text: str) -> list:
    response = genai.embed_content(model=EMBED_MODEL, content=text)
    embedding = response.get("embedding")
    if not embedding:
        raise ValueError("No embedding returned from Gemini.")
    return embedding

# Upsert document (store text in metadata)
def upsert_document(doc_id: str, text: str, metadata: dict = None):
    embedding = get_gemini_embedding(text)
    full_metadata = metadata or {}
    full_metadata["text"] = text
    response = index.upsert(
        vectors=[{
            "id": doc_id,
            "values": embedding,
            "metadata": full_metadata
        }]
    )
    print(f"[INFO] Upserted {doc_id}, response: {response}")

# Semantic search with cleaned response
def semantic_search(query: str, top_k: int = 3):
    embedding = get_gemini_embedding(query)
    results = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )
    matches = [
        {
            "id": m["id"],
            "score": round(m["score"], 4),
            "source": m["metadata"].get("source", "unknown"),
            "text": m["metadata"].get("text", "No text")
        }
        for m in results["matches"]
    ]
    return matches

# Generate user-readable answer using Gemini
def generate_answer(query: str, matches: list):
    context = "\n".join([f"Source: {m['source']}\nText: {m['text']}" for m in matches])
    prompt = f"""
    You are an expert assistant for insurance/legal policies.
    Based on the context, answer the question clearly and explain why.
    If answer is not found, say "Not mentioned in the policy."

    Question: {query}

    Context:
    {context}

    Respond ONLY in JSON format:
    {{
        "answer": "...",
        "explanation": "...",
        "sources": [...]
    }}
    """
    response = genai.GenerativeModel(REASONING_MODEL).generate_content(prompt)
    # Validate JSON output
    try:
        return json.loads(response.text)
    except:
        return {"answer": response.text.strip(), "explanation": "Could not parse as JSON", "sources": []}

# Example usage
if __name__ == "__main__":
    # Insert policy text
    upsert_document(
        "doc1",
        "Flood damage is covered under natural disaster clause.",
        {"source": "policy.pdf"}
    )

    # Query
    query = "Does the policy cover flood damage?"
    matches = semantic_search(query)
    print("\n[INFO] Retrieved Chunks:", matches)

    # Generate reasoning-based answer
    final_answer = generate_answer(query, matches)
    print("\n[FINAL ANSWER]:", json.dumps(final_answer, indent=2))
