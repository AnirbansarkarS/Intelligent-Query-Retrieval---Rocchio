from fastapi import FastAPI, Header, HTTPException
from typing import Optional
from app.schemas import QueryRequest
import time
import logging

app = FastAPI()

@app.post("/")
async def root():
    return {"massage" : "connected succesdsfully"}

@app.post("/hackrx/run")
async def run_hackrx(
    data:QueryRequest ,
    authorization: Optional[str] = Header(None)):

    start = time.perf_counter()

    # Check for Bearer token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    token = authorization.split(" ")[1]

    # Your logic for processing documents and questions
    # Example response:

    end =  time.perf_counter()
    execution_time = end - start
    logging.info(f"Execution time: {execution_time:.2f} seconds")

    return {
        "status": "success",
        "received": {
            "token": token,
            "documents": data.documents,
            "questions": data.questions
        }
    }
