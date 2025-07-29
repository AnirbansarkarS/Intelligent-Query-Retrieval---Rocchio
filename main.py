from fastapi import FastAPI
from app.api import router

app = FastAPI()

@app.get("/")
def read_root():
	return {"message": "Hello from FastAPI!"}

app.include_router(router)


#soumbha
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.auth import verify_token
from app.schemas import QueryRequest

app = FastAPI()

# CORS (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/hackrx/run")
def run_submission(request: QueryRequest, _: bool = Depends(verify_token)):
    pdf_url = request.documents
    questions = request.questions

    # Print inputs for debug
    print("PDF URL:", pdf_url)
    print("Questions:", questions)

    # TODO: Replace with actual PDF handling logic
    return {"answers": ["Answer 1", "Answer 2"]}

