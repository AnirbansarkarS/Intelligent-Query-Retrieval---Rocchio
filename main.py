from fastapi import FastAPI
from app.api import router

app = FastAPI()

@app.get("/")
def read_root():
	return {"message": "Hello from FastAPI!"}

app.include_router(router)

# Anirban
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from app.core.parser import parse_document
from app.utils.chunker import chunk_text
from app.core.llm_handler import query_gemini_flash

app = FastAPI()

class QueryRequest(BaseModel):
    documents: str
    questions: list[str]

@app.post("/hackrx/run")
async def run_hackrx(req: QueryRequest):
    try:
        text = parse_document(req.documents)
        chunks = chunk_text(text)
        results = []
        for q in req.questions:
            answers = [query_openai(q, c) for c in chunks]
            filtered = [a for a in answers if 'Not Found' not in a]
            final_answer = filtered[0] if filtered else 'Not Found'
            results.append(final_answer)
        return {"answers": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#Anirban