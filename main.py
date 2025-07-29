from fastapi import FastAPI
from app.api import router

app = FastAPI()

@app.get("/")
def read_root():
	return {"message": "Hello from FastAPI!"}

app.include_router(router)


# TODO: abe 100% ai generated....  without context aigulo merge korish na...
# Anirban
# from fastapi import FastAPI, Request, HTTPException
# from pydantic import BaseModel
# from app.core.parser import parse_document
# from app.utils.chunker import chunk_text
# from app.core.llm_handler import query_openai

# app = FastAPI()

# class QueryRequest(BaseModel):
#     documents: str
#     questions: list[str]

# @app.post("/hackrx/run")
# async def run_hackrx(req: QueryRequest):
#     try:
#         text = parse_document(req.documents)
#         chunks = chunk_text(text)
#         results = []
#         for q in req.questions:
#             answers = [query_openai(q, c) for c in chunks]
#             filtered = [a for a in answers if 'Not Found' not in a]
#             final_answer = filtered[0] if filtered else 'Not Found'
#             results.append(final_answer)
#         return {"answers": results}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
# #Anirban


#soumbha
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from auth import verify_token
from schemas import RunRequest

app = FastAPI()

# CORS (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/hackrx/run")
def run_submission(request: RunRequest, _: bool = Depends(verify_token)):
    pdf_url = request.documents
    questions = request.questions

    # Print inputs for debug
    print("PDF URL:", pdf_url)
    print("Questions:", questions)

    # TODO: Replace with actual PDF handling logic
    return {"answers": ["Answer 1", "Answer 2"]}
