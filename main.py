from fastapi import FastAPI
from app.api import router

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

app.include_router(router)
