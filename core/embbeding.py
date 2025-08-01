# XPOLION : Intelligent Query & Retrieval (Optimized Chunk-Based)
# Features: Chunked Ingestion, Semantic Search, LLM Answer Generation

import os
import time
import logging
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai

from core.llm_handeler import query_gemini_flash
from utils.chunker import tokenize_and_chunk

# ==============================
# CONFIGURATION
# ==============================
load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

genai.configure(api_key=os.getenv("GEMINI_KEY"))
EMBED_MODEL = "models/embedding-001"
EMBED_DIM = 768

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX", "doc-embeddings")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if missing
if INDEX_NAME not in [idx["name"] for idx in pc.list_indexes()]:
    logging.info(f"Creating Pinecone index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBED_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    logging.info("Waiting for index to be ready...")
    time.sleep(10)

index = pc.Index(INDEX_NAME)
logging.info(f"Connected to Pinecone index: {INDEX_NAME}")

# ==============================
# EMBEDDING HELPER
# ==============================
def get_gemini_embedding(text: str, task_type: str) -> list:
    for attempt in range(3):
        try:
            response = genai.embed_content(model=EMBED_MODEL, content=text, task_type=task_type)
            embedding = response.get("embedding")
            if not embedding:
                raise ValueError("Empty embedding returned from Gemini.")
            return embedding
        except Exception as e:
            logging.warning(f"Embedding attempt {attempt+1} failed: {e}")
            time.sleep(1)
    raise RuntimeError(f"Failed to fetch embedding after 3 retries for text: {text[:50]}...")

# ==============================
# INGESTION (Chunked)
# ==============================
def ingest_document(doc_id: str, text: str, metadata: dict = None):
    ns = doc_id  # namespace per document
    stats = index.describe_index_stats()
    if ns in stats.get("namespaces", {}):
        logging.info(f"Document '{doc_id}' already ingested. Skipping.")
        return

    chunks = tokenize_and_chunk(text)
    logging.info(f"Tokenized into {len(chunks)} chunks.")
    vectors = []

    for i, chunk in enumerate(chunks):
        emb = get_gemini_embedding(chunk, "retrieval_document")
        vectors.append({
            "id": f"{doc_id}_{i}",
            "values": emb,
            "metadata": {**(metadata or {}), "text": chunk, "chunk_index": i}
        })

    index.upsert(vectors=vectors, namespace=ns)
    logging.info(f"Ingested {len(chunks)} chunks for '{doc_id}'.")

# ==============================
# RETRIEVAL (Top Chunks)
# ==============================
def semantic_search(query: str, doc_id: str, top_k: int = 12):
    embedding = get_gemini_embedding(query, "retrieval_query")
    results = index.query(vector=embedding, top_k=top_k, include_metadata=True, namespace=doc_id)

    matches = [
        {"id": m["id"], "score": round(m["score"], 4), "text": m["metadata"]["text"]}
        for m in results["matches"]
    ]
    return matches

# ==============================
# ANSWER GENERATION
# ==============================
def answer_question(query: str, matches: list) -> str:
    context_text = "\n".join([m["text"] for m in matches])
    return query_gemini_flash(query, context_text)

# ==============================
# MAIN PIPELINE
# ==============================
def run_pipeline(doc_id: str, text: str, questions: list, meta: dict = None):
    ingest_document(doc_id, text, meta)
    results = []
    for q in questions:
        matches = semantic_search(q, doc_id)
        answer = answer_question(q, matches)
        results.append({"question": q, "answer": answer})
    return results
