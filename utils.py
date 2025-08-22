# utils.py

import os
import json
import logging
import inflect
import requests

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

p = inflect.engine()

def pluralize(count, word):
    return f"{count} {p.plural(word, count)}"

def format_timestamp(timestamp):
    """Format a timestamp string to a more readable format."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime(conf.get("output_timestamp_format", "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        logging.info(f"Invalid timestamp format: {timestamp}. Using original.")
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

def parse_container_name(log_file_path):
    log_file_name = os.path.basename(log_file_path)
    container_name = log_file_name.split("_")[-1].replace(".log", "")

    return container_name

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

def get_env_file():
    if os.path.exists('.env'):
        print(".env file already exists. Skipping download.")
        logging.info(".env file already exists. Skipping download.")
        return
    else:
        print("Downloading .env file from the server...")
        logging.info("Downloading .env file from the server...")
        local_filename = conf.get("mongodb_conn_var_url", "").split('/')[-1]

        response = requests.get(conf.get("mongodb_conn_var_url", ""), stream=True)
        response.raise_for_status()  # check for HTTP errors

        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f".env file downloaded successfully as {local_filename}.")
        logging.info(f".env file downloaded successfully as {local_filename}.")
