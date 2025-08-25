# mongodb_handler.py

import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Custom imports
from utils import logging, get_env_file, conf


class MongoHandler:
    def __init__(self, uri, db_name="log_config"):
        self.uri = uri
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.shared_config = self.db["log_error_patterns"]       # Default shared patterns
        self.user_config = self.db["user_error_patterns"]        # User-specific patterns
        self.logs = self.db["logs"]

        print(f"MongoDB connection established to database: {db_name}")
        logging.info(f"MongoDB connection established to database: {db_name}")
    
    def close_connection(self):
        self.client.close()
    
    def open_connection(self):
        self.client = MongoClient(self.uri)

    # Default Shared Dictionary

    def get_default_error_patterns(self):
        doc = self.shared_config.find_one({"type": "log_error_patterns"})
        return doc["patterns"] if doc else {}

    def update_error_patterns(self, new_patterns):
        self.shared_config.update_one(
            {"type": "log_error_patterns"},
            {"$set": {"patterns": new_patterns}},
            upsert=True
        )

    def add_error_pattern(self, category, pattern):
        doc = self.shared_config.find_one({"type": "log_error_patterns"})
        if not doc:
            self.shared_config.insert_one({
                "type": "log_error_patterns",
                "patterns": {category: [pattern]}
            })
            return

        if category not in doc.get("patterns", {}):
            self.shared_config.update_one(
                {"type": "log_error_patterns"},
                {"$set": {f"patterns.{category}": [pattern]}}
            )
        else:
            self.shared_config.update_one(
                {"type": "log_error_patterns"},
                {"$addToSet": {f"patterns.{category}": pattern}}
            )

    # User-Specific Dictionary
    def get_all_users(self):
        all_user_documents = self.user_config.find({}, {"_id": 0, "user_id": 1})
        all_users = [document['user_id'] for document in all_user_documents]
        return all_users
    
    def user_exists(self, user_id):
        return self.user_config.find_one({"user_id": user_id})

    def add_document(self, user_id, patterns={}):
        self.user_config.insert_one({
                "user_id": user_id,
                "patterns": patterns
            })
    
    def ensure_user_document(self, user_id):
        if not self.user_exists(user_id):
            print(f"User ID {user_id} has no error patterns saved. ")
            self.add_document(user_id)

    def get_user_patterns(self, user_id):
        doc = self.user_config.find_one({"user_id": user_id})
        return doc["patterns"] if doc else {}

    def update_user_patterns(self, user_id, new_patterns):
        self.user_config.update_one(
            {"user_id": user_id},
            {"$set": {"patterns": new_patterns}},
            upsert=True
        )

    def add_user_error_pattern(self, user_id, category, pattern):
        doc = self.user_config.find_one({"user_id": user_id})
        if not doc:
            self.user_config.insert_one({
                "user_id": user_id,
                "patterns": {category: [pattern]}
            })
            return

        if category not in doc.get("patterns", {}):
            self.user_config.update_one(
                {"user_id": user_id},
                {"$set": {f"patterns.{category}": [pattern]}}
            )
        else:
            self.user_config.update_one(
                {"user_id": user_id},
                {"$addToSet": {f"patterns.{category}": pattern}}
            )

    def save_log_result(self, pod_name, log_data):
        self.logs.insert_one({
            "pod": pod_name,
            "log": log_data
        })
        
def load_mongodb():
    try:
        get_env_file() 
        load_dotenv()
        mongo_uri = os.getenv("MONGODB_URI")

        if not mongo_uri:
            print("MongoDB URI not found in environment variables.")
            logging.error("MongoDB URI not found in environment variables.")
        else:

            mongo = MongoHandler(uri=mongo_uri)
    
    except Exception as e:
        print(f"Error loading MongoDB configuration: {e}.\nUsing default patterns from conf.json.")
        logging.error(f"Error loading MongoDB configuration: {e}. Using default patterns from conf.json.")
        return None
    
    return mongo
