from pydantic import BaseModel
from typing import List

class RunRequest(BaseModel):
	document_text: str
	query: str

class RunResponse(BaseModel):
	status: str
	output: str


