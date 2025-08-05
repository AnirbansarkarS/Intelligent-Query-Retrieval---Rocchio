from fastapi import Header, HTTPException, status, Depends
from dotenv import load_dotenv
import os

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

def verify_api_key(token):
    if token != ACCESS_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True