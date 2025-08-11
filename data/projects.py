# data/projects.py
import os
import uuid
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/wonder_ai")
DB_NAME = os.getenv("DB_NAME", "wonder_ai")

_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
_db = _client[DB_NAME]
_projects = _db["projects"]

# Indexes
_projects.create_index([("user_email", ASCENDING), ("project_id", ASCENDING)], unique=True, name="uniq_user_project")
_projects.create_index([("user_email", ASCENDING), ("updated_at", ASCENDING)], name="user_updated_at")

def now_utc():
    return datetime.utcnow()

def create_project(user_email: str, name: str, prompt: str = "", options: dict | None = None) -> dict:
    pid = uuid.uuid4().hex[:12]
    doc = {
        "user_email": user_email.lower(),
        "project_id": pid,
        "name": name.strip() or f"Project {pid[:4]}",
        "prompt": prompt or "",
        "options": options or {},
        "code": None,             # {"html": "...", "css": "...", "js": "..."}
        "preview_url": None,
        "status": "new",          # new | generated | exported
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
    _projects.insert_one(doc)
    return doc

def list_projects(user_email: str, limit: int = 100):
    return list(
        _projects.find({"user_email": user_email.lower()})
                 .sort("updated_at", -1)
                 .limit(limit)
    )

def get_project(user_email: str, project_id: str):
    return _projects.find_one({"user_email": user_email.lower(), "project_id": project_id})

def update_project(user_email: str, project_id: str, updates: dict):
    updates["updated_at"] = now_utc()
    _projects.update_one(
        {"user_email": user_email.lower(), "project_id": project_id},
        {"$set": updates}
    )
    return get_project(user_email, project_id)

def save_generation(user_email: str, project_id: str, prompt: str, options: dict, code: dict, preview_url: str | None):
    return update_project(
        user_email, project_id,
        {"prompt": prompt, "options": options, "code": code, "preview_url": preview_url, "status": "generated"}
    )
