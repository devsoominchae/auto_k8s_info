# user_log_uploader.py

import json
import os
from mongodb_handler import MongoHandler
from dotenv import load_dotenv
load_dotenv()

uri = os.getenv("MONGODB_URI")

def load_user_json(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None

def upload_user_log_dict(file_path, username, mongo_uri):
    # Load JSON
    user_data = load_user_json(file_path)
    if not user_data:
        print("Invalid or missing JSON.")
        return

    if "patterns" not in user_data:
        print("JSON must contain a top-level 'patterns' key.")
        return

    # Connect to Mongo
    mongo = MongoHandler(uri=mongo_uri)
    
    # Check/Create user doc
    mongo.ensure_user_document(username)

    # Overwrite their personal patterns with this file
    mongo.update_user_patterns(username, user_data["patterns"])
    print(f"Patterns successfully stored for user '{username}'.")

if __name__ == "__main__":
    USERNAME = input("Enter your username: ").strip()
    FILE_PATH = input("Enter path to your JSON file: ").strip()
    upload_user_log_dict(FILE_PATH, USERNAME, uri)
