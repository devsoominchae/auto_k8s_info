from pymongo import MongoClient

# mongodb_handler.py - for connecting to MongoDB and handling log patterns
#basic layout for now. Allows for updating, and getting error patterns
class MongoHandler:
    def __init__(self, uri="mongodb+srv://sasadm:Orion123@logdictionary.ziwndyc.mongodb.net/?retryWrites=true&w=majority&appName=logDictionary", db_name="log_config"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.config = self.db["config"]
        self.logs = self.db["logs"]

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
