from pymongo import MongoClient
from utils import logging

# mongodb_handler.py - Handles MongoDB connections and log pattern storage
class MongoHandler:
    def __init__(self, uri, db_name="log_config"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.config = self.db["log_error_patterns"]
        self.logs = self.db["logs"]

        print(f"MongoDB connection established to database: {db_name}")
        logging.info(f"MongoDB connection established to database: {db_name}")

    def get_error_patterns(self):
        doc = self.config.find_one({"type": "log_error_patterns"})
        return doc["patterns"] if doc else {}

    def update_error_patterns(self, new_patterns):
        self.config.update_one(
            {"type": "log_error_patterns"},
            {"$set": {"patterns": new_patterns}},
            upsert=True
        )

    def add_error_pattern(self, category, pattern):
        doc = self.config.find_one({"type": "log_error_patterns"})
        if not doc:
            # Insert a new document if it doesn't exist
            self.config.insert_one({
                "type": "log_error_patterns",
                "patterns": {category: [pattern]}
            })
            return

        # If category doesn't exist, create it
        if category not in doc.get("patterns", {}):
            self.config.update_one(
                {"type": "log_error_patterns"},
                {"$set": {f"patterns.{category}": [pattern]}}
            )
        else:
            # If pattern doesn't already exist, add it using $addToSet
            self.config.update_one(
                {"type": "log_error_patterns"},
                {"$addToSet": {f"patterns.{category}": pattern}}
            )

    def save_log_result(self, pod_name, log_data):
        self.logs.insert_one({
            "pod": pod_name,
            "log": log_data
        })
