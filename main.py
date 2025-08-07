from fastapi import FastAPI, Header, HTTPException
from typing import Optional

from app.schemas import QueryRequest
from app.auth import verify_api_key

from core.logic_evaluator import evaluate_logic

import time
import logging

app = FastAPI()

@app.get("/")
async def root():
    return {"massage" : "connected succesdsfully"}
    
async def remove_ngrok_warning(request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

@app.post("/hackrx/run")
async def run_hackrx(
    data:QueryRequest ,
    authorization: Optional[str] = Header(None)):

    start = time.perf_counter()

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    token = authorization.split(" ")[1]
    if not verify_api_key(token):
        return {"status": "API KEY WRONG"}

    output = evaluate_logic(data.documents,data.questions)

    end =  time.perf_counter()
    execution_time = end - start
    logging.info(f"Execution time: {execution_time:.2f} seconds")

    return output
