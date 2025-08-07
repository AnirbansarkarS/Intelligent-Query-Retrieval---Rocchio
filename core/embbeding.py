# Intelligent Query & Retrieval (Optimized Chunk-Based) by XpolioN
# Features: Chunked Ingestion, Batch Query Expansion, Multi-Query Semantic Search, LLM Answer Generation

import os
import time
import logging
import pickle
import numpy as np
import faiss
from dotenv import load_dotenv
from pathlib import Path
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle

from core.llm_handeler import query_gemini_flash
from utils.chunker import tokenize_and_chunk

# ====================
# INIT & CONFIG
# ====================
load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

EMBED_MODEL = "models/embedding-001"
EMBED_DIM = 768

# Get API keys function
GEMINI_KEYS = [k.strip() for k in os.getenv("GEMINI_KEYS", "").split(",") if k.strip()]
if not GEMINI_KEYS:
    raise ValueError("No Gemini keys found in .env (use GEMINI_KEYS=key1,key2,key3)")
key_cycle = cycle(GEMINI_KEYS)

# Relative save paths
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = STORAGE_DIR / "index.faiss"
META_PATH = STORAGE_DIR / "faiss_store.pkl"

# Load or create FAISS index and metadata store
if INDEX_PATH.exists() and META_PATH.exists():
    faiss_index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, "rb") as f:
        faiss_store = pickle.load(f)
    logging.info("[LOADED] FAISS index and metadata from disk.")
else:
    faiss_index = faiss.IndexIDMap(faiss.IndexFlatL2(EMBED_DIM))
    faiss_store = {}
    logging.info("[INIT] New FAISS index and metadata store.")

vector_id_counter = max([vid for ns in faiss_store.values() for vid in ns.keys()], default=0) + 1

key = ""
# ====================
# EMBEDDING WRAPPER
# ====================
def rotate_key():
    return next(key_cycle)

def get_gemini_embedding(text: str, task_type: str) -> list:
    for _ in range(len(GEMINI_KEYS)):
            key = rotate_key()
            try:
                genai.configure(api_key=key)
                resp = genai.embed_content(model=EMBED_MODEL, content=text, task_type="retrieval_document")
                emb = resp.get("embedding")
                if emb:
                    return np.array(emb, dtype="float32")
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    continue
                raise
    raise RuntimeError("All Gemini keys exhausted or failed.")

# ====================
# INGESTION
# ====================
def file_exists(doc_id: str) -> bool:
    return doc_id in faiss_store

def ingest_document(doc_id: str, text: str, metadata: dict = None):
    global vector_id_counter
    if file_exists(doc_id):
        logging.info(f"Document '{doc_id}' already ingested. Skipping.")
        return

    chunks = tokenize_and_chunk(text)
    logging.info(f"Tokenized into {len(chunks)} chunks.")
    vectors = []
    ids = []
    store = {}

    def embed_chunk(i, chunk):
        emb = get_gemini_embedding(chunk, "retrieval_document")
        return i, emb, chunk

    with ThreadPoolExecutor(max_workers=min(16, len(chunks))) as executor:
        futures = [executor.submit(embed_chunk, i, chunk) for i, chunk in enumerate(chunks)]
        for future in as_completed(futures):
            i, emb, chunk = future.result()
            vec_id = vector_id_counter
            vector_id_counter += 1
            vectors.append(np.array(emb, dtype='float32'))
            ids.append(vec_id)
            store[vec_id] = {
                "text": chunk,
                "chunk_index": i,
                **(metadata or {})
            }

    faiss_index.add_with_ids(np.vstack(vectors), np.array(ids))
    faiss_store[doc_id] = store
    logging.info(f"Ingested {len(vectors)} chunks for '{doc_id}'.")

    # Save index and metadata
    faiss.write_index(faiss_index, str(INDEX_PATH))
    with open(META_PATH, "wb") as f:
        pickle.dump(faiss_store, f)
    logging.info("[SAVED] Index and metadata saved to disk.")


# ====================
# SEARCH + AGGREGATION
# ====================
def intersection_score(query, text):
    query_terms = set(query.lower().split())
    text_terms = set(text.lower().split())
    return len(query_terms & text_terms) / max(len(query_terms), 1)

def semantic_search_multi(variants: list, doc_id: str, top_k: int = 24, original_query: str = None):
    all_matches = {}
    weights = {"original": 1.5, "variant": 1.0}
    doc_store = faiss_store.get(doc_id, {})

    for variant in variants:
        embedding = get_gemini_embedding(variant, "retrieval_query")
        D, I = faiss_index.search(np.array([embedding], dtype='float32'), top_k)
        for score, vec_id in zip(D[0], I[0]):
            if vec_id == -1 or vec_id not in doc_store:
                continue

            weight = weights["original"] if variant.strip() == original_query.strip() else weights["variant"]
            weighted_score = (1.0 / (score + 1e-5)) * weight  # invert distance for scoring
            text = doc_store[vec_id]["text"]
            intersect = intersection_score(variant, text)

            if vec_id in all_matches:
                all_matches[vec_id]["score"] += weighted_score
                all_matches[vec_id]["intersection"] += intersect * 2
            else:
                all_matches[vec_id] = {
                    "id": vec_id,
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
    for _ in range(len(GEMINI_KEYS)):
            key = rotate_key()
            try:
                return query_gemini_flash(query, context_text, key=key)
                
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    continue
                raise
    raise RuntimeError("All Gemini keys exhausted or failed.")



# ====================
# PIPELINE ENTRY
# ====================
def run_pipeline(doc_id: str, text: str, questions: list, meta: dict = None):
    """
    Run the complete ingestion and QnA pipeline.

    Args:
        doc_id (str): Unique identifier for the document (used as namespace).
        text (str): Raw document text content.
        questions (list): List of questions (strings) to ask based on the document.
        meta (dict, optional): Optional metadata to associate with each chunk during ingestion.

    Returns:
        list: A list of dictionaries where each dict has the structure:
              {
                  "question": <original_question>,
                  "answer": <generated_answer>
              }
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