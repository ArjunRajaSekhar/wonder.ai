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

def now_utc():
    return datetime.utcnow()

def _ensure_indexes():
    # Clean legacy bad values so index creation won't choke
    try:
        # Remove the field when it's null
        _projects.update_many({"idempotency_key": None}, {"$unset": {"idempotency_key": ""}})
    except Exception:
        pass

    # Regular indexes
    _projects.create_index(
        [("user_email", ASCENDING), ("project_id", ASCENDING)],
        unique=True,
        name="uniq_user_project"
    )
    _projects.create_index(
        [("user_email", ASCENDING), ("updated_at", ASCENDING)],
        name="user_updated_at"
    )

    # Partial unique: only index docs that actually have a string key
    _projects.create_index(
        [("user_email", ASCENDING), ("idempotency_key", ASCENDING)],
        unique=True,
        name="uniq_user_idempotency",
        partialFilterExpression={"idempotency_key": {"$exists": True, "$type": "string"}},
    )

_ensure_indexes()

def create_project(
    user_email: str,
    name: str,
    prompt: str = "",
    options: dict | None = None,
    project_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    if not idempotency_key:
        # Always generate a real key so we never write null
        idempotency_key = uuid.uuid4().hex

    pid = project_id or uuid.uuid4().hex[:12]
    now = now_utc()

    # Upsert by (user_email, idempotency_key)
    _projects.update_one(
        {"user_email": user_email.lower(), "idempotency_key": idempotency_key},
        {
            "$setOnInsert": {
                "project_id": pid,
                "idempotency_key": idempotency_key,  # store for audit/debug
                "name": (name or f"Project {pid[:4]}").strip(),
                "prompt": prompt or "",
                "options": options or {},
                "code": None,
                "preview_url": None,
                "status": "new",
                "created_at": now,
            },
            "$set": {"updated_at": now},
        },
        upsert=True,
    )

    return _projects.find_one(
        {"user_email": user_email.lower(), "idempotency_key": idempotency_key}
    )

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
