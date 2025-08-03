from fastapi import FastAPI
from app.api import router

app = FastAPI()

@app.get("/")
def read_root():
	return {"message": "Hello from FastAPI!"}

app.include_router(router)

# @app.post("/api/v1/hackrx/run")
# def run_submission(request: QueryRequest, _: bool = Depends(verify_token)):
#     pdf_url = request.documents
#     questions = request.questions

#     # Print inputs for debug
#     print("PDF URL:", pdf_url)
#     print("Questions:", questions)



