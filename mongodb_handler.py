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

    def save_log_result(self, pod_name, log_data):
        self.logs.insert_one({
            "pod": pod_name,
            "log": log_data
        })
