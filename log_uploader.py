# user_log_uploader.py

import os
import json
from dotenv import load_dotenv

from utils import logging, conf
from mongodb_handler import MongoHandler

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

def user_dict_has_valid_format(user_dict_path):
    user_dict = load_user_json(user_dict_path)
    top = list(user_dict.keys())
    patterns = list(user_dict.values())

    if top[0] != "patterns":
        print(f"Top key must be \"patterns\", not {top[0]}")
        logging.error(f"Top key must be \"patterns\", not {top[0]}")
        return False
    for pattern in patterns:
        category, error_patterns = pattern.items()
        if type(category) != str:
            print(f"The type of the name of the category must be str not {type(category)}")
            logging.error(f"The type of the name of the category must be str not {type(category)}")
        for error_pattern in error_patterns:
            if type(error_pattern) != str:
                print(f"The type of the error pattern must be str not {type(error_pattern)}")
                logging.error(f"The type of the error pattern must be str not {type(error_pattern)}")
                return False
    return True
        

def return_default_dict(mongo_uri):
    mongo = MongoHandler(uri=mongo_uri)
    return mongo.get_error_patterns()

def replace_user_dict_with_file(file_path, username, mongo_uri):
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
    print(f"Patterns successfully replaced for user '{username}'.")

def get_user_id_from_user(mongo_uri):
    mongo = MongoHandler(uri=mongo_uri)
    user_id = input("Enter your username: ").strip()
    if user_id == "":
        print(f"User ID cannot be blank. Using default error patterns.")
        logging.info(f"User ID cannot be blank. Using default error patterns.")
        return "default"
    elif not mongo.user_exists(user_id):
        create_user_input = input(f"User ID does not exist. Would you like to create a new user? (y - default/n)").strip()
        if create_user_input in conf["yes_pattern"]:
            default_dict = return_default_dict(mongo_uri)
            mongo.add_document(user_id, default_dict["patterns"])
        else:
            print("Using default error pattern")
            return "default"
    return user_id



if __name__ == "__main__":
    USERNAME = get_user_id_from_user()
    if USERNAME != "default":
        FILE_PATH = input("Enter path to your JSON file: ").strip()
        replace_user_dict_with_file(FILE_PATH, USERNAME, uri)
    else:
        return_default_dict(uri)