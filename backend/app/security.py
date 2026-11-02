import os
from fastapi import Header, HTTPException
from dotenv import load_dotenv

load_dotenv()
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
if not INTERNAL_API_KEY:
    raise RuntimeError("Missing required env var INTERNAL_API_KEY")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")