# user_log_uploader.py

import os
import json
from dotenv import load_dotenv

from utils import logging, conf
from mongodb_handler import MongoHandler

load_dotenv()

uri = os.getenv("MONGODB_URI")

def load_json_from_path(file_path):
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
    user_dict = load_json_from_path(user_dict_path)
    categories = list(user_dict.keys())
    patterns = list(user_dict.values())
    
    for category in categories:
        if type(category) != str:
            print(f"The type of the name of the category must be str not {type(category)}")
            logging.error(f"The type of the name of the category must be str not {type(category)}")
            return False
    
    for pattern in patterns:
        if type(pattern) != list:
            print(f"The type of that contains error patterns must be a list (ex. ['error pattern 1', 'error pattern 2']) not {type(pattern)}")
            logging.error(f"The type of that contains error patterns must be a list (ex. ['error pattern 1', 'error pattern 2']) not {type(pattern)}")
            return False
        for pattern_element in pattern:
            if type(pattern_element) != str:
                print(f"The type of the pattern element must be a string (ex. ['error pattern 1', 'error pattern 2']) not {type(pattern_element)}")
                logging.error(f"The type of the pattern element must be a string (ex. ['error pattern 1', 'error pattern 2']) not {type(pattern_element)}")
                return False
    return True
        
# def replace_user_dict_with_file(user_dict_path, username, mongo):
#     # Load JSON
#     if user_dict_has_valid_format(user_dict_path):
#         user_dict = load_json_from_path(user_dict_path)

#         # Check/Create user doc
#         mongo.ensure_user_document(username)

#         # Overwrite their personal patterns with this file
#         mongo.update_user_patterns(username, user_dict)
#         print(f"Patterns successfully replaced for user '{username}'.")

def get_user_id_from_user(mongo):
    user_id = input("Enter your username: ").strip()
    if user_id == "":
        print(f"User ID cannot be blank. Using default error patterns.")
        logging.info(f"User ID cannot be blank. Using default error patterns.")
        return "default"
    elif not mongo.user_exists(user_id):
        create_user_input = input(f"User ID does not exist. Would you like to create a new user? (yes - default/no): ").strip()
        if create_user_input in conf["yes_list"]:
            default_dict = mongo.get_default_error_patterns()
            mongo.add_document(user_id, default_dict)
        else:
            print("Using default error patterns.")
            return "default"
    return user_id

def user_will_create_new_id(mongo):
    new_id_yes_or_no = input("Would you like to create a new user? (yes - default/no)").strip()
    if new_id_yes_or_no in conf["yes_list"]:
        return True
    else:
        return False
    
def user_will_update_dict():
    answer = input(f"Would you like to upload/download the error patterns? (yes - default/no): ").strip()
    if answer in conf["yes_list"]:
        return True
    else:
        return False



# if __name__ == "__main__":
#     USERNAME = get_user_id_from_user()
#     if USERNAME != "default":
#         FILE_PATH = input("Enter path to your JSON file: ").strip()
#         replace_user_dict_with_file(FILE_PATH, USERNAME, uri)
#     else:
#         return_default_dict(uri)