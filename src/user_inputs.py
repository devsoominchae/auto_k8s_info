# user_inputs.py

import os
import json

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter


# Custom imports
from utils import logging, conf, remove_invalid_windows_path_chars, load_json_from_path

DOWNLOAD_UPLOAD_OPTIPONS = [
    "Download",
    "Upload",
    "Exit"
    ]

def select_option(options, message_to_prompt="Please select an action:", tab_complete=False, ignore_invalid=False):
    while True:
        options_dict = {str(i+1) : element for i, element in enumerate(options)}
        
        print(f"\n{message_to_prompt}")
        for key, value in options_dict.items():
            print(f"{key}. {value}")

        choice = ""
        if tab_complete:
            menu_completer = WordCompleter(
                options,
                ignore_case=True
            )
            choice = prompt("Enter choice: ", completer=menu_completer).strip()
        else:
            choice = input("Enter choice: ").strip()

        if choice in options_dict:
            print(f"Your choice: {options_dict[choice]}")
            return options_dict[choice]
        
        if choice in options_dict.values():
            print(f"Your choice: {choice}")
            return choice

        if not ignore_invalid:
            print("❌ Invalid choice. Please try again.")
        else:
            return choice


def get_case_info_dir_from_user(cache):
    case_info_dir = get_user_input_via_cache(cache, 'saved_case_info_dir', "Saved path to get-k8s-info output", "Please enter the path to the get-k8s-info output file")

    return case_info_dir

def get_error_patterns_path_from_user(cache):
    error_patterns_path = get_user_input_via_cache(cache, 'error_patterns', "Saved path to error patterns", "Please enter the path to the error patterns file")
    
    return error_patterns_path

def get_user_input_via_cache(cache, target, msg_saved_cache, msg_please_enter_value):
    cached_value = cache.get(target, '')
    if cached_value:
        print(f"{msg_saved_cache}: {cached_value}")
        logging.info(f"{msg_saved_cache}: {cached_value}")
        use_saved_path = remove_invalid_windows_path_chars(input(f"Do you want to use this cached input? (yes - default/no): ").strip().lower())

        if use_saved_path not in conf.get("yes_list", ["yes", "y", "Y", "Yes", "", "YES"]):
            logging.info("Not using saved path")
            cached_value = ""
            value = remove_invalid_windows_path_chars(input(f"{msg_please_enter_value}: ").strip())
            cache[target] = value
            with open(conf.get("cache", "cache.json"), 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
        else:
            value = cached_value
            print(f"Using cached input: {value}")
            logging.info(f"Using cached input: {value}")

    else:
        # Get user input to specify the path to the get-k8s-info output
        logging.info(f"Nothing cached for {target}. Asking user for input.")
        value = remove_invalid_windows_path_chars(input(f"{msg_please_enter_value}: ").strip())
        logging.info(f"User provided {target}: {value}")
        cache[target] = value
        with open(conf.get("cache", "cache.json"), 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)

    return value

def get_namespace_path_from_user(case_info_dir):
    # List the folders under kubernetes folder and let user select one
    kubernetes_path = os.path.join(case_info_dir, 'kubernetes')
    if not os.path.exists(kubernetes_path):
        print(f"The 'kubernetes' folder does not exist under {case_info_dir}.")
        logging.error(f"The 'kubernetes' folder does not exist under {case_info_dir}. Exiting the program.")
        return

    folders = [f for f in os.listdir(kubernetes_path) if os.path.isdir(os.path.join(kubernetes_path, f))]
    if not folders:
        print("No folders found under 'kubernetes'.")
        logging.error("No folders found under 'kubernetes'. Exiting the program.")
        return

    selected_folder = select_option(folders, message_to_prompt="Available folders under kubernetes:", tab_complete=True)
    namespace_path = os.path.join(kubernetes_path, selected_folder)
    logging.info(f"Processing logs on {namespace_path}")

    return namespace_path

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


def get_user_id_from_user(mongo):
    all_users = mongo.get_all_users()
    all_users.sort()
    all_users.append("default")
    user_id = select_option(all_users, message_to_prompt="Select a user by number or by user ID or enter a new user ID.", tab_complete=True, ignore_invalid=True)
    if user_id == "default":
        print(f"Using default error patterns.")
        logging.info(f"Using default error patterns.")
    
    if len(user_id) < 5:
        print(f"Username must be longer than 5 characters. Current input: \nUsername : {user_id} \nLength : {len(user_id)} \nUsing default error patterns.")
        logging.info(f"Username must be longer than 5 characters. Current: {len(user_id)}. Using default error patterns.")
        user_id = "default"
    
    return user_id

def user_will_create_new_id(mongo, user_id):
    if not mongo.user_exists(user_id):
        create_user_input = input(f"User ID does not exist. Would you like to create a new user \"{user_id}\"? (yes - default/no): ").strip()
        if create_user_input in conf["yes_list"]:
            default_dict = mongo.get_default_error_patterns()
            mongo.add_document(user_id, default_dict)
        else:
            print("New user not created. Using default error patterns.")
            logging.info("New user not created. Using default error patterns.")

    
def user_will_update_dict():
    answer = input(f"Would you like to upload/download the error patterns? (yes - default/no): ").strip()
    if answer in conf["yes_list"]:
        return True
    else:
        return False

def get_error_patterns_from_user_input(user_id, mongo, error_patterns, cache):
    if user_id != "default":
        if mongo.user_exists(user_id):
            error_patterns = mongo.get_user_patterns(user_id)
        else:
            user_will_create_new_id(mongo, user_id)
        print("Error patterns :\n", json.dumps(error_patterns, indent=4))
        if user_will_update_dict():
            while True:
                match select_option(DOWNLOAD_UPLOAD_OPTIPONS, tab_complete=True):
                    case "Download":
                        with open("error_patterns.json", "w", encoding="utf-8") as f:
                            json.dump(error_patterns, f, ensure_ascii=False, indent=4)
                            print(f"Error patterns file saved to {os.path.join(os.getcwd(), 'error_patterns.json')}")
                            logging.info(f"Error patterns file saved to {os.path.join(os.getcwd(), 'error_patterns.json')}")
                    case "Upload":
                        user_dict_path = get_error_patterns_path_from_user(cache)
                        if user_dict_has_valid_format(user_dict_path):
                            error_patterns = load_json_from_path(user_dict_path)
                            print("Error patterns :\n", json.dumps(error_patterns, indent=4))
                        else:
                            print(f"Using saved error patterns for user ID {user_id}")
                            logging.info(f"Using saved error patterns for user ID {user_id}")
                    case "Exit":
                        break
                    
    else:
        print("Error patterns :\n", json.dumps(error_patterns, indent=4))
    
    return error_patterns
