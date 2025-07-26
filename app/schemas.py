from pydantic import BaseModel

class RunRequest(BaseModel):
    document_text: str
    query: str

class RunResponse(BaseModel):
    status: str
    output: str
