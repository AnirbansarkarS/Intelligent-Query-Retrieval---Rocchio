
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_KEY"))

model = genai.GenerativeModel("gemini-pro")  

SYSTEM_INSTRUCTION = (
    "You are a concise insurance document assistant. "
    "Given a context and a question, answer in short. If unsure, say 'Not Found'."
)

def query_gemini_flash(question: str, context: str) -> str:
    try:
        prompt = f"{SYSTEM_INSTRUCTION}\n\nContext:\n{context}\n\nQuestion:\n{question}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"
        

# TODO need to do it again with emmbeinging....
