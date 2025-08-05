from pydantic import BaseModel
from typing import List,Dict,Any

class QueryRequest(BaseModel):
    documents: str
    questions: List[str]

class QueryResponse(BaseModel):
    answers: List[str] 
