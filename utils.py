# utils.py

import os
import json
import logging

# Custom imports



RESTORE_CONF_FILE = 'conf_restored.json'
CONF = {
  "cache": "cache.json",
  "cache_default": {
    "saved_case_info_dir": ""
  },
  "output_folder": "output",
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s %(levelname)s %(message)s"
  },
  "print_level" : 1,
  "yes_list": [
    "yes",
    "y",
    "Y",
    "Yes",
    "",
    "YES"
  ],
  "invalid_windows_path_chars": [
    "<",
    ">",
    "\"",
    "/",
    "|",
    "?",
    "*"
  ],
  "describe_pods_error_patterns": {
    "Warning": [
      "Warning"
    ]
  },
  "get_pods_error_patterns": {
    "Error": [
      "Error"
    ],
    "Running No Pods": [
      "0/",
      "Running"
    ],
    "Hanged in Init": [
      "Init:"
    ],
    "Crashed": [
      "CrashLoopBackOff"
    ]
  },
  "log_error_patterns": {
    "CAS Control Issues": [
      "no ready CAS servers",
      "cas-control is not ready"
    ],
    "Start Sequencer Warnings": [
      "SKIP_INIT_BLOCK",
      "bypassing sequencing",
      "exit code 0"
    ],
    "Readiness Check Failures": [
      "check \"sas-endpoints-ready\" failed",
      "no available addresses",
      "endpoints have no available addresses",
      "0 available addresses",
      "failed readiness check"
    ],
    "Stalled Init Warnings": [
      "Waiting for",
      "POD(s) to Complete"
    ],
    "Authentication Failures": [
      "Unauthorized",
      "authentication failed",
      "access denied",
      "invalid credentials",
      "token expired"
    ]
  }
}

def get_conf():
    global conf
    if os.path.exists('conf.json'):
        with open('conf.json', 'r', encoding='utf-8') as f:
            conf = json.load(f)
    else:
        restore_conf()
        exit(1)

def restore_conf():
    if os.path.exists(RESTORE_CONF_FILE):
        print(f"{RESTORE_CONF_FILE} already exists. Rename it to 'conf.json' to use it.")
        return
    with open(RESTORE_CONF_FILE, 'w', encoding='utf-8') as f:
        json.dump(CONF, f, indent=2)
    print(f"Configuration restored to {RESTORE_CONF_FILE}. Rename it to 'conf.json' to use it.")

def format_timestamp(timestamp):
    """Format a timestamp string to a more readable format."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime(conf.get("output_timestamp_format", "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        print(f"Invalid timestamp format: {timestamp}. Using original.")
        return timestamp

def load_cache():
    cache = {}
    if not os.path.exists(conf.get("cache", "cache.json")):
        print(f'{conf.get("cache", "cache.json")} does not exist. Creating a new one.')        
        logging.info(f'{conf.get("cache", "cache.json")} does not exist. Creating a new one.')        

        with open(conf.get("cache", "cache.json"), 'w', encoding='utf-8') as f:
            json.dump(conf.get("cache_default", {"saved_case_info_dir": ""}), f, indent=2)
    with open(conf.get("cache", "cache.json"), 'r') as cache_file:
        cache = json.load(cache_file)
      
    return cache

get_conf()

def load_logging_level():
    if conf['logging']:
        match conf['logging']['level'].upper():
            case 'DEBUG':
                return logging.DEBUG
            case 'INFO':
                return logging.INFO
            case 'WARNING':
                return logging.WARNING
            case 'ERROR':
                return logging.ERROR
            case 'CRITICAL':
                return logging.CRITICAL
            case _:
                logging.warning(f"Unknown logging level: {conf['logging']['level']}. Defaulting to INFO.")
    return logging.INFO  # Default level if not specified


# Configure logging
logging.basicConfig(
    level=load_logging_level(),
    format=conf.get('logging', {}).get('format', "%(asctime)s %(levelname)s %(message)s"),
    # format=conf['logging']['format'],
    handlers=[
        logging.FileHandler('auto_k8s_info.log', encoding='utf-8')  # Log to file
    ]
)

def remove_invalid_windows_path_chars(filename):
    invalid_chars = conf.get('invalid_windows_path_chars', ["<", ">", "\"", "/", "|", "?", "*"])
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename

def get_case_info_dir_from_user(cache):
    saved_case_info_dir = cache.get('saved_case_info_dir', '')
    if saved_case_info_dir:
        print(f"Saved path to get-k8s-info output: {saved_case_info_dir}")
        logging.info(f"Saved path to get-k8s-info output: {saved_case_info_dir}")
        use_saved_path = remove_invalid_windows_path_chars(input("Do you want to use this saved path? (yes - default/no): ").strip().lower())

        if use_saved_path not in conf.get("yes_list", ["yes", "y", "Y", "Yes", "", "YES"]):
            logging.info("Not using saved path")
            saved_case_info_dir = ""
            case_info_dir = remove_invalid_windows_path_chars(input(f"Please enter the path to the get-k8s-info output folder: ").strip())
            cache.setdefault('saved_case_info_dir', case_info_dir)
            with open(conf.get("cache", "cache.json"), 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
        else:
            case_info_dir = saved_case_info_dir
            print(f"Using saved path: {case_info_dir}")
            logging.info(f"Using saved path: {case_info_dir}")

    else:
        # Get user input to specify the path to the get-k8s-info output
        logging.info("No saved path found. Asking user for input.")
        case_info_dir = remove_invalid_windows_path_chars(input("Please enter the path to the get-k8s-info output file: ").strip())
        logging.info(f"User provided path: {case_info_dir}")
        cache.setdefault('saved_case_info_dir', case_info_dir)
        with open(conf.get("cache", "cache.json"), 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)

    return case_info_dir