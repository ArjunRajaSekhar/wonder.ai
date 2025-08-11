# auth/db.py
import os
import bcrypt
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/wonder_ai")
DB_NAME = os.getenv("DB_NAME", "wonder_ai")

_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
_db = _client[DB_NAME]
_users = _db["users"]

# Ensure a unique index on email once
_users.create_index([("email", ASCENDING)], unique=True, name="uniq_email")

def hash_password(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())

def verify_password(plain: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed)
    except Exception:
        return False

def get_user_by_email(email: str):
    return _users.find_one({"email": email.lower().strip()})

def create_user(email: str, password: str, full_name: str | None = None):
    doc = {
        "email": email.lower().strip(),
        "password": hash_password(password),
        "full_name": (full_name or "").strip(),
        "created_at": datetime.utcnow(),
        "last_login_at": None,
        "status": "active",
        "role": "user",
    }
    res = _users.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc

def authenticate(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None
    if verify_password(password, user["password"]):
        _users.update_one({"_id": user["_id"]}, {"$set": {"last_login_at": datetime.utcnow()}})
        return user
    return None
