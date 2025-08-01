# XPOLION : Intelligent Query & Retrieval (Optimized Chunk-Based)
# Features: Chunked Ingestion, Batch Query Expansion, Multi-Query Semantic Search, LLM Answer Generation

import os
import time
import logging
import json
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai

from core.llm_handeler import query_gemini_flash  # For final structured answer
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
# BATCH QUERY EXPANSION WITH GEMINI FLASH-LITE
# ==============================
def batch_expand_queries(questions: list, num_variants: int = 5) -> dict:
    """
    Expand multiple questions in a single Gemini Flash-Lite call with strict JSON rules.
    Returns: dict like {"1": ["alt1", "alt2", ...], "2": [...], ...}
    """
    prompt = (
        f"You are a query rewriter. Generate {num_variants} alternative phrasings for each question.\n\n"
        f"STRICT RULES:\n"
        f"1. Respond ONLY with valid JSON. No text before or after.\n"
        f"2. Do NOT include markdown, code fences, comments, or explanations.\n"
        f"3. Each key must be a string of the question number (e.g., \"1\", \"2\").\n"
        f"4. Each value must be an array of {num_variants} strings (the alternative phrasings).\n"
        f"5. Use plain text only in values. No quotes inside the text.\n"
        f"6. Do NOT include the original question in the alternatives.\n\n"
        f"Example:\n"
        f'{{"1": ["alt1", "alt2", "alt3"], "2": ["alt1", "alt2", "alt3"]}}\n\n'
        f"Questions:\n"
    )
    for i, q in enumerate(questions, start=1):
        prompt += f"{i}. {q}\n"

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.3,}
        )
        raw_text = response.text.strip()

        # ✅ Auto-clean: Strip any code fences if still present
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").replace("json", "").strip()

        # ✅ Validate and load JSON safely
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        logging.error(f"[ERROR] JSON decode failed: {e}\nRaw output:\n{raw_text}")
        # ✅ Fallback: return empty lists for all questions
        return {str(i): [] for i in range(len(questions))}
    except Exception as e:
        logging.error(f"[ERROR] Batch expansion failed: {e}")
        return {str(i): [] for i in range(len(questions))}




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
# MULTI-QUERY SEMANTIC SEARCH
# ==============================
def semantic_search_multi(variants: list, doc_id: str, top_k: int = 10, original_query: str = None):
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
            vector=embedding,
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

    # Batch expand all questions in one go
    expansions = batch_expand_queries(questions)

    results = []
    for idx, q in enumerate(questions, start=1):
        variants = [q] + expansions.get(str(idx), [])
        logging.info(f"Question: {q} | Variants: {len(variants)}")
        matches = semantic_search_multi(variants, doc_id)
        answer = answer_question(q, matches)
        results.append({"question": q, "answer": answer})
    return results
