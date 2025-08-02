
# # ==============================
# # BATCH QUERY EXPANSION WITH GEMINI FLASH-LITE
# # ==============================
# def batch_expand_queries(questions: list, num_variants: int = 4 ) -> dict:
#     """
#     Expand multiple questions in a single Gemini Flash-Lite call with strict JSON rules.
#     Returns: dict like {"1": ["alt1", "alt2", ...], "2": [...], ...}
#     """
#     prompt = (
#         f"You are a query rewriter. Generate {num_variants} alternative phrasings for each question.\n\n"
#         f"STRICT RULES:\n"
#         f"1. Respond ONLY with valid JSON. No text before or after.\n"
#         f"2. Do NOT include markdown, code fences, comments, or explanations.\n"
#         f"3. Each key must be a string of the question number (e.g., \"1\", \"2\").\n"
#         f"4. Each value must be an array of {num_variants} strings (the alternative phrasings).\n"
#         f"5. Use plain text only in values. No quotes inside the text.\n"
#         f"6. Do NOT include the original question in the alternatives.\n\n"
#         f"Example:\n"
#         f'{{"1": ["alt1", "alt2", "alt3"], "2": ["alt1", "alt2", "alt3"]}}\n\n'
#         f"Questions:\n"
#     )
#     for i, q in enumerate(questions, start=1):
#         prompt += f"{i}. {q}\n"

#     try:
#         model = genai.GenerativeModel("gemini-2.5-flash-lite")
#         response = model.generate_content(
#             prompt,
#             generation_config={"temperature": 0.3,}
#         )
#         raw_text = response.text.strip()

#         # ✅ Auto-clean: Strip any code fences if still present
#         if raw_text.startswith("```"):
#             raw_text = raw_text.strip("`").replace("json", "").strip()

#         # ✅ Validate and load JSON safely
#         return json.loads(raw_text)
#     except json.JSONDecodeError as e:
#         logging.error(f"[ERROR] JSON decode failed: {e}\nRaw output:\n{raw_text}")
#         # ✅ Fallback: return empty lists for all questions
#         return {str(i): [] for i in range(len(questions))}
#     except Exception as e:
#         logging.error(f"[ERROR] Batch expansion failed: {e}")
#         return {str(i): [] for i in range(len(questions))}



# XPOLION : Intelligent Query & Retrieval (Optimized Chunk-Based)
# Features: Chunked Ingestion, Batch Query Expansion, Multi-Query Semantic Search, LLM Answer Generation

import os
import time
import logging
# import json
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
import google.genai as genai_batch
from google.genai import types

from concurrent.futures import ThreadPoolExecutor, as_completed


from core.llm_handeler import query_gemini_flash  # For final structured answer
from utils.chunker import tokenize_and_chunk

# ==============================
# CONFIGURATION
# ==============================
load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
EMBED_MODEL = "models/embedding-001"
EMBED_DIM = 1536

client = genai_batch.Client()

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

def get_gemini_embedding(tasks: list, task_type: str) -> list:
    for attempt in range(3):
        try:
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=tasks,
                config=types.EmbedContentConfig(task_type=task_type,output_dimensionality=EMBED_DIM)
            )
            embeddings = [e.values for e in response.embeddings]

            if not embeddings or any(e is None for e in embeddings):
                raise ValueError("Empty embedding(s) returned from Gemini.")
            
            return embeddings
        
        except Exception as e:
            logging.warning(f"Embedding attempt {attempt + 1} failed: {e}")
            time.sleep(1)

    raise RuntimeError(f"Failed to fetch embedding after 3 retries for text: {tasks[0][:50]}...")

# ==============================
# INGESTION (Chunked)
# ==============================
def wait_for_pinecone_commit(namespace: str, expected_count: int, timeout=30, interval=2):
    """
    Wait until Pinecone reports at least expected_count vectors in the namespace.
    """
    start = time.time()
    while time.time() - start < timeout:
        stats = index.describe_index_stats()
        ns_stats = stats.get("namespaces", {}).get(namespace, {})
        current_count = ns_stats.get("vector_count", 0)

        if current_count >= expected_count:
            logging.info(f"[READY] Namespace '{namespace}' has {current_count} vectors.")
            return True

        logging.info(f"[WAIT] {current_count}/{expected_count} vectors ingested. Retrying in {interval}s...")
        time.sleep(interval)

    logging.warning(f"[TIMEOUT] Namespace '{namespace}' did not reach {expected_count} vectors within {timeout}s.")
    return False

def ingest_document(doc_id: str, text: str, metadata: dict = None):
    ns = doc_id  # namespace per document
    stats = index.describe_index_stats()
    if ns in stats.get("namespaces", {}):
        logging.info(f"Document '{doc_id}' already ingested. Skipping.")
        return

    chunks = tokenize_and_chunk(text)
    logging.info(f"Tokenized into {len(chunks)} chunks.")

    try:
        embeddings = get_gemini_embedding(chunks, "RETRIEVAL_DOCUMENT")
    except Exception as e:
        logging.error(f"Failed to embed document '{doc_id}': {e}")
        return

    vectors = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        vectors.append({
            "id": f"{doc_id}_{i}",
            "values": emb,
            "metadata": {**(metadata or {}), "text": chunk, "chunk_index": i}
        })

    index.upsert(vectors=vectors, namespace=ns)
    logging.info(f"Ingested {len(vectors)} chunks for '{doc_id}'.")
    wait_for_pinecone_commit(ns, len(vectors), 10, 2)


# ==============================
# MULTI-QUERY SEMANTIC SEARCH
# ==============================
def semantic_search_multi(variants: list, doc_id: str, top_k: int = 5, original_query: str = None):
    """
    Perform weighted, normalized aggregation of multi-query search results.
    Boosts original query matches and normalizes per query.
    """
    all_matches = {}
    weights = {
        "original": 1.5,  # Boost for the main query
        "variant": 1.0    # Normal weight for paraphrases
    }

    for variant in variants:
        embedding = get_gemini_embedding(variant, "retrieval_query")
        results = index.query(
            vector=embedding[0],
            top_k=top_k,
            include_metadata=True,
            namespace=doc_id
        )

        matches = results.get("matches", [])
        if not matches:
            continue

        # Normalize scores for this query
        max_score = max(m["score"] for m in matches)
        if max_score == 0:
            max_score = 1  # Avoid divide-by-zero

        for match in matches:
            chunk_id = match["id"]
            norm_score = match["score"] / max_score

            # Apply weight
            if original_query and variant.strip() == original_query.strip():
                weighted_score = norm_score * weights["original"]
            else:
                weighted_score = norm_score * weights["variant"]

            if chunk_id in all_matches:
                all_matches[chunk_id]["score"] += weighted_score
            else:
                all_matches[chunk_id] = {
                    "id": chunk_id,
                    "score": weighted_score,
                    "text": match["metadata"]["text"]
                }

    # Sort by aggregated weighted score
    sorted_matches = sorted(all_matches.values(), key=lambda x: x["score"], reverse=True)
    return sorted_matches[:top_k]


def process_question(idx, q, expansions, doc_id):
    variants = [q] + expansions.get(str(idx), [])
    logging.info(f"[THREAD] Processing Question: {q}")
    matches = semantic_search_multi(variants, doc_id)
    answer = answer_question(q, matches)
    return {"question": q, "answer": answer}


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

    expansions = {str(i): [] for i in range(len(questions))}

    results = []
    with ThreadPoolExecutor(max_workers=min(8, len(questions))) as executor:
        futures = [executor.submit(process_question, idx, q, expansions, doc_id)
                   for idx, q in enumerate(questions, start=1)]

        for future in as_completed(futures):
            results.append(future.result())

    return results




