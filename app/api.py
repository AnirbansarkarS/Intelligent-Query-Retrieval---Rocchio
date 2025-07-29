from fastapi import APIRouter, HTTPException
from app.schemas import QueryRequest, QueryResponse

router = APIRouter()

@router.post("/hackrx/run", response_model=QueryResponse)
def run_hackrx_logic(request: QueryRequest):
	# TEMP DUMMY LOGIC (replace with real later)
	if not request.query:
		raise HTTPException(status_code=400, detail="Query is required")
	
	return {
		"status": "success",
		"output": f"Received query: {request.query}"
		}