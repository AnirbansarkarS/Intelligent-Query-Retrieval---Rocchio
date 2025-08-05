
# ANIRBAN
# from fastapi import APIRouter, HTTPException
# from app.schemas import QueryRequest, QueryResponse  
# from core.parser import parse_document
# from utils.chunker import tokenize_and_chunk
# from core.llm_handeler import query_gemini_flash

# router = APIRouter()

# @router.post("/hackrx/run", response_model=QueryResponse)
# async def run_hackrx(req: QueryRequest):
#     try:
#         text = parse_document(req.documents)
#         chunks = tokenize_and_chunk(text)
#         results = []

#         for q in req.questions:
#             answers = [query_gemini_flash(q, c) for c in chunks]
#             filtered = [a for a in answers if 'Not Found' not in a]
#             final_answer = filtered[0] if filtered else 'Not Found'
#             results.append(final_answer)

#         return QueryResponse(
#             success=True,
#             message="Pipeline ran successfully",
#             data={"answers": results}
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
