
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")  

SYSTEM_INSTRUCTION = """
You are an expert assistant for insurance/legal policies.
Based on the context and your knowledge, answer the question clearly and explain why.
If the context has the answer, cite it. If not, answer null.

Respond ONLY with valid JSON in this exact format:
{
    "answer": "...",
    "explanation": "...",
    "sources": ["..."]
}

Rules:
- Always include all three keys.
- Do not include any markdown, code fences, or extra text outside the JSON.
- If context provided useful info, include the IDs in "sources", else keep it empty.
"""

# edited qury to better suite the api requiremnet
def query_gemini_flash(question: str, context: str) -> str:
    try:
        prompt = f"{SYSTEM_INSTRUCTION}\n\nContext:\n{context}\n\nQuestion:\n{question}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"
        