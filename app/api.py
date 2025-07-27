from fastapi import APIRouter, HTTPException
from app.schemas import RunRequest, RunResponse

router = APIRouter()

@router.post("/hackrx/run", response_model=RunResponse)
def run_hackrx_logic(request: RunRequest):
	# TEMP DUMMY LOGIC (replace with real later)
	if not request.query:
		raise HTTPException(status_code=400, detail="Query is required")
	
	return {
		"status": "success",
		"output": f"Received query: {request.query}"
		}