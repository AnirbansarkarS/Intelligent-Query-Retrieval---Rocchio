from fastapi import APIRouter
from app.schemas import QueryRequest, QueryResponse

router = APIRouter()

@router.post("/hackrx/run", response_model=QueryResponse)
def run_pipeline(request: QueryRequest):
    # Placeholder logic for now
    return QueryResponse(
        success=True,
        message="Pipeline ran successfully",
        data={"matched_clauses": [], "final_decision": "Pending"}
    )