#Intelligent Query & Retrieval (Optimized Chunk-Based) by XpolioN
# Features: Chunked Ingestion, Batch Query Expansion, Multi-Query Semantic Search, LLM Answer Generation

import os
import time
import logging
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.llm_handeler import query_gemini_flash
from utils.chunker import tokenize_and_chunk

# ====================
# INIT & CONFIG
# ====================
load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

genai.configure(api_key=os.getenv("GEMINI_KEY"))
EMBED_MODEL = "models/embedding-001"
EMBED_DIM = 768

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX", "doc-embeddings")

# Init Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
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

# ====================
# EMBEDDING WRAPPER
# ====================
def get_gemini_embedding(text: str, task_type: str) -> list:
    for attempt in range(3):
        try:
            response = genai.embed_content(model=EMBED_MODEL, content=text, task_type=task_type)
            embedding = response.get("embedding")
            if not embedding:
                raise ValueError("Empty embedding from Gemini.")
            return embedding
        except Exception as e:
            logging.warning(f"Embedding attempt {attempt+1} failed: {e}")
            time.sleep(1)
    raise RuntimeError("Failed to get embedding after 3 retries.")

# ====================
# INGESTION
# ====================
def file_exists(doc_id: str) -> bool:
    ns = doc_id
    if ns in index.describe_index_stats().get("namespaces", {}):
        logging.info(f"Document '{doc_id}' already ingested. Skipping.")
        return True
    return False

def wait_for_pinecone_commit(namespace: str, expected_count: int, timeout=30, interval=2):
    start = time.time()
    while time.time() - start < timeout:
        stats = index.describe_index_stats()
        ns_stats = stats.get("namespaces", {}).get(namespace, {})
        current_count = ns_stats.get("vector_count", 0)
        if current_count >= expected_count:
            logging.info(f"[READY] Namespace '{namespace}' has {current_count} vectors.")
            return True
        logging.info(f"[WAIT] {current_count}/{expected_count} vectors. Retrying in {interval}s...")
        time.sleep(interval)
    logging.warning(f"[TIMEOUT] Namespace '{namespace}' did not reach {expected_count} vectors.")
    return False

def ingest_document(doc_id: str, text: str, metadata: dict = None):
    ns = doc_id
    if file_exists(ns):
        return

    chunks = tokenize_and_chunk(text)
    logging.info(f"Tokenized into {len(chunks)} chunks.")
    vectors = []

    def embed_chunk(i, chunk):
        emb = get_gemini_embedding(chunk, "retrieval_document")
        return {
            "id": f"{doc_id}_{i}",
            "values": emb,
            "metadata": {**(metadata or {}), "text": chunk, "chunk_index": i}
        }

    with ThreadPoolExecutor(max_workers=min(16, len(chunks))) as executor:
        futures = [executor.submit(embed_chunk, i, chunk) for i, chunk in enumerate(chunks)]
        for future in as_completed(futures):
            vectors.append(future.result())

    index.upsert(vectors=vectors, namespace=ns)
    logging.info(f"Ingested {len(vectors)} chunks for '{doc_id}'.")
    wait_for_pinecone_commit(ns, len(vectors), 10, 0.5)

# ====================
# SEARCH + AGGREGATION
# ====================
def intersection_score(query, text):
    query_terms = set(query.lower().split())
    text_terms = set(text.lower().split())
    return len(query_terms & text_terms) / max(len(query_terms), 1)

def semantic_search_multi(variants: list, doc_id: str, top_k: int = 24, original_query: str = None):
    all_matches = {}
    weights = { "original": 1.5, "variant": 1.0 }

    for variant in variants:
        embedding = get_gemini_embedding(variant, "retrieval_query")
        results = index.query(vector=embedding, top_k=top_k, include_metadata=True, namespace=doc_id)
        matches = results.get("matches", [])
        if not matches: continue

        max_score = max(m["score"] for m in matches) or 1

        for match in matches:
            chunk_id = match["id"]
            norm_score = match["score"] / max_score
            weight = weights["original"] if variant.strip() == original_query.strip() else weights["variant"]
            weighted_score = norm_score * weight
            text = match["metadata"]["text"]
            intersect = intersection_score(variant, text)

            if chunk_id in all_matches:
                all_matches[chunk_id]["score"] += weighted_score
                all_matches[chunk_id]["intersection"] += intersect * 2
            else:
                all_matches[chunk_id] = {
                    "id": chunk_id,
                    "score": weighted_score,
                    "intersection": intersect,
                    "text": text
                }

    sorted_matches = sorted(
        all_matches.values(),
        key=lambda x: x["score"] + x["intersection"],
        reverse=True
    )
    return [sorted_matches[:5], sorted_matches[:top_k]]

def process_question(idx, q, expansions, doc_id):
    variants = [q] + expansions.get(str(idx), [])
    logging.info(f"[THREAD] Processing: {q}")
    matches = semantic_search_multi(variants, doc_id, original_query=q)
    answer = answer_question(q, matches[0])
    if "er-404" in answer:
        answer = answer_question(q, matches[1])
    return {"question": q, "answer": answer}

# ====================
# FINAL ANSWER
# ====================
def answer_question(query: str, matches: list) -> str:
    context_text = "\n".join([m["text"] for m in matches])
    return query_gemini_flash(query, context_text)

# ====================
# PIPELINE ENTRY
# ====================
def run_pipeline(doc_id: str, text: str, questions: list, meta: dict = None):
    """
    Run the complete ingestion and QnA pipeline.

    Args:
        doc_id (str): Unique identifier for the document (used as Pinecone namespace).
        text (str): Raw document text content.
        questions (list): List of questions (strings) to ask based on the document.
        meta (dict, optional): Optional metadata to associate with each chunk during ingestion.

    Returns:
        list: A list of dictionaries where each dict has the structure:
              {
                  "question": <original_question>,
                  "answer": <generated_answer>
              }

    Example:
        result = run_pipeline(
            doc_id="doc1",
            text="This is a sample document containing useful info.",
            questions=["What is this about?", "Who is it for?"],
            meta={"source": "internal"}
        )
    """
    ingest_document(doc_id, text, meta)
    expansions = {str(i): [] for i in range(len(questions))}
    results = [None] * len(questions)

    with ThreadPoolExecutor(max_workers=min(8, len(questions))) as executor:
        futures = {
            executor.submit(process_question, idx, q, expansions, doc_id): idx
            for idx, q in enumerate(questions)
        }
        for future in as_completed(futures):
            idx = futures[future]
            results[idx] = future.result()

    return results
