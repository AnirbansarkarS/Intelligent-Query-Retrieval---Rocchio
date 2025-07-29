
# XPOLION dont know if it gonna work, but it made by AI
# This code is for embedding documents using Gemini and storing them in Pinecone

import os
from dotenv import load_dotenv
import pinecone
import google.generativeai as genai

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_KEY"))
model = genai.GenerativeModel("gemini-embedding-001")

# Configure Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
INDEX_NAME = os.getenv("PINECONE_INDEX", "doc-embeddings")

pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

def get_gemini_embedding(text: str) -> list:
    """
    Get embedding vector for text using Gemini.
    """
    try:
        # Gemini embedding API (pseudo, update if actual API differs)
        response = model.embed_content([text])
        return response.embeddings[0]
    except Exception as e:
        raise RuntimeError(f"Gemini embedding failed: {e}")

def upsert_document(doc_id: str, text: str):
    """
    Upsert a document's embedding into Pinecone.
    """
    embedding = get_gemini_embedding(text)
    index = pinecone.Index(INDEX_NAME)
    index.upsert([(doc_id, embedding)])

def semantic_search(query: str, top_k: int = 3):
    """
    Perform semantic search in Pinecone using Gemini embedding of the query.
    """
    embedding = get_gemini_embedding(query)
    index = pinecone.Index(INDEX_NAME)
    results = index.query(vector=embedding, top_k=top_k, include_metadata=True)
    return results
