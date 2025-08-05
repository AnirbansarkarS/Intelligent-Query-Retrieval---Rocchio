from fastapi import FastAPI, Header, HTTPException
from typing import List, Optional
from app.schemas import QueryRequest

app = FastAPI()

@app.post("/hackrx/run")
async def run_hackrx(
    data:QueryRequest ,
    authorization: Optional[str] = Header(None)
):
    # # Check for Bearer token
    # if not authorization or not authorization.startswith("Bearer "):
    #     raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    # token = authorization.split(" ")[1]

    # Your logic for processing documents and questions
    # Example response:
    return {
        "status": "success",
        "received": {
            # "token": token,
            "documents": data.documents,
            "questions": data.questions
        }
    }
