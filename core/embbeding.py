# Intelligent Query & Retrieval (Optimized Chunk-Based) by XpolioN
# Features: Chunked Ingestion, Batch Query Expansion, Multi-Query Semantic Search, LLM Answer Generation

import os
import re
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

def get_paths(doc_id):
    return (
        STORAGE_DIR / f"{doc_id}.faiss",
        STORAGE_DIR / f"{doc_id}.pkl"
    )

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
            resp = genai.embed_content(model=EMBED_MODEL, content=text, task_type=task_type)
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
def normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    return vec / norm if norm != 0 else vec

def ingest_document(doc_id: str, text: str, metadata: dict = None):
    index_path, meta_path = get_paths(doc_id)

    if index_path.exists() and meta_path.exists():
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
            vec_id = i
            vectors.append(normalize(np.array(emb, dtype="float32")))
            ids.append(vec_id)
            store[vec_id] = {
                "text": chunk,
                "chunk_index": i,
                **(metadata or {})
            }

    index = faiss.IndexIDMap(faiss.IndexFlatIP(EMBED_DIM))
    index.add_with_ids(np.vstack(vectors), np.array(ids))

    faiss.write_index(index, str(index_path))
    with open(meta_path, "wb") as f:
        pickle.dump(store, f)

    logging.info(f"[SAVED] Ingested '{doc_id}' with {len(vectors)} chunks.")

# ====================
# SEARCH + AGGREGATION
# ====================
def intersection_score(query, text):
    query_terms = set(query.lower().split())
    text_terms = set(text.lower().split())
    return len(query_terms & text_terms) / max(len(query_terms), 1)

def semantic_search_multi(variants: list, doc_id: str, top_k: int = 40, original_query: str = None):
    index_path, meta_path = get_paths(doc_id)

    if not index_path.exists() or not meta_path.exists():
        raise ValueError(f"Document '{doc_id}' not ingested yet.")

    index = faiss.read_index(str(index_path))
    with open(meta_path, "rb") as f:
        doc_store = pickle.load(f)

    all_matches = {}
    weights = {"original": 1.5, "variant": 1.0}

    for variant in variants:
        embedding = normalize(get_gemini_embedding(variant, "retrieval_query"))
        D, I = index.search(np.array([embedding], dtype="float32"), top_k)

        for score, vec_id in zip(D[0], I[0]):
            if vec_id == -1 or vec_id not in doc_store:
                continue

            text = doc_store[vec_id]["text"]
            intersect = intersection_score(variant, text)
            weight = weights["original"] if variant.strip() == original_query.strip() else weights["variant"]
            weighted_score = score * weight

            if vec_id in all_matches:
                all_matches[vec_id]["score"] += weighted_score
                all_matches[vec_id]["intersection"] += intersect * 2
            else:
                all_matches[vec_id] = {
                    "id": vec_id,
                    "doc_id": doc_id,
                    "text": text,
                    "score": weighted_score,
                    "intersection": intersect,
                }

    # Final scoring
    matches = list(all_matches.values())
    for match in matches:
        match["final_score"] = 0.65 * match["score"] + 0.35 * match["intersection"]

    return sorted(matches, key=lambda x: x["final_score"], reverse=True)[:top_k]


def rerank_with_keyword_overlap(matches, query):
    # Tokenize query with alphanumeric + camelCase/snake_case support
    query_keywords = set(re.findall(r"\b[\w']+\b", query.lower()))

    for match in matches:
        # Tokenize text more robustly (handles variable names etc.)
        text_tokens = set(re.findall(r"\b[\w']+\b", match["text"].lower()))

        # Keyword overlap score
        keyword_overlap = len(query_keywords & text_tokens)
        match["keyword_overlap"] = keyword_overlap

        # Final score: tune based on observed quality
        match["final_score"] = (
            0.6 * match["score"]
            + 0.3 * match["intersection"]
            + 0.4 * match["keyword_overlap"]
        )

    return sorted(matches, key=lambda x: x["final_score"], reverse=True)

def process_question(idx, q, expansions, doc_id):
    variants = [q] + expansions.get(str(idx), [])
    logging.info(f"[THREAD] Processing: {q}")
    matches = semantic_search_multi(variants, doc_id, original_query=q)
    rerank = rerank_with_keyword_overlap(matches=matches, query=q)
    answer = answer_question(q, rerank[:25])
    if "er-404" in answer:
        logging.info(f"retrying for {q}")
        answer = answer_question(q, rerank)
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
