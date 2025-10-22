import os
from urllib.parse import quote_plus
from pymongo import MongoClient

_cached_client = None

def get_mongo_client():
    global _cached_client
    if _cached_client is not None:
        return _cached_client
    uri = os.getenv("MONGO_URL") or "mongodb://localhost:27017"
    _cached_client = MongoClient(uri)
    return _cached_client


def get_db(db_name: str = None):
    client = get_mongo_client()
    name = db_name or os.getenv("MONGO_DB", "socialite")
    return client[name]
