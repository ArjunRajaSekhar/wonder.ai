# data/documents.py
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/wonder_ai")
DB_NAME = os.getenv("DB_NAME", "wonder_ai")

_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
_db = _client[DB_NAME]
_docs = _db["documents"]

_docs.create_index([("user_email", ASCENDING), ("project_id", ASCENDING), ("doc_id", ASCENDING)], unique=True)

def _now():
    return datetime.utcnow()

def upsert_document(user_email: str, project_id: str, doc_id: str, meta: Dict[str, Any]):
    _docs.update_one(
        {"user_email": user_email.lower(), "project_id": project_id, "doc_id": doc_id},
        {"$set": {**meta, "updated_at": _now()}, "$setOnInsert": {"created_at": _now()}},
        upsert=True,
    )

def list_documents(user_email: str, project_id: str):
    return list(_docs.find({"user_email": user_email.lower(), "project_id": project_id}).sort("updated_at", -1))
