from pydantic import BaseModel
from typing import List,Dict,Any

class QueryRequest(BaseModel):
    documents: str
    questions: List[str]

class QueryResponse(BaseModel):
    output: str
    success: bool
    message: str
    data: Dict[str, Any] 
