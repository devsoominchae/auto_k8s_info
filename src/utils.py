# utils.py

import re
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
        "saved_case_info_dir": "",
        "error_patterns": ""
    },
    "restart_filter_threshold": 10,
    "max_files_to_show": 10,
    "mongodb_conn_var_url": "http://trck1076843.trc.sas.com:8000/.env",
    "user_activity_url": "http://trck1076843.trc.sas.com:8000/record",
    "output_timestamp_format": "%Y-%m-%d %H:%M:%S",
    "print_level": 1,
    "output_folder": "output",
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s %(levelname)s %(message)s"
    },
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
        ],
        "Reason": [
            "OOMKilled"
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
        "Telemetry Warnings": [
            "OpenTelemetry support not installed",
            "noop Open Telemetry MeterProvider",
            "no metrics will be collected"
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
        ],
        "Tool Execution Failures": [
            "sonder-log-icu.tool.error.executing.command.log",
            "sonder-log-icu.tool.executor.failed.running.tools.log",
            "Service executor failed to execute successfully: exit status 1"
        ],
        "Certificate Write Failures": [
            "writeAsPem failed",
            "error writing PEM file"
        ],
        "Certificate Errors": [
            "error generating certificates",
            "failed to create cert secret",
            "failed to write certificate file",
            "invalid certificate configuration"
        ],
        "PVC Errors": [
            "PersistentVolumeClaim is not bound",
            "PersistentVolumeClaim is not available",
            "PersistentVolumeClaim is in pending state",
            "PVC pending",
            "PVC"
        ],
        "FailedMount Errors": [
            "MountVolume.SetUp failed for volume",
            "references non-existent secret key"
        ],
        "Compute Context Errors": [
            "Compute context to be used by the CAS Formats service",
            "no ready CAS servers, so cas-control is not ready"
        ],
        "PyConfig errors": [
            "Error creating md5sum file"
        ],
        "SAS Data Quality Services Errors": [
            "sonder-log-icu.tool.executor.failed.starting.service.log"
        ],
        "SAS ESP CSS Errors": [
            "could not find a valid ESP SERVER license"
        ],
        "Consul issues": [
            "No cluster leader"
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

    return load_and_fix_json(file_path)

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

def escape_inner_quotes(json_string: str) -> str:
    """
    Escapes unescaped double quotes inside double-quoted JSON strings.
    Example: "check "something" failed" -> "check \"something\" failed"
    """
    counter = [0]  # use a list to make it mutable in nested function

    def replacer(match):
        counter[0] += 1
        if counter[0] in (2, 3):
            return "\\\""
        return match.group(0)
    
    strings_to_modify = re.findall(r'".*".*".*"', json_string)
    modified_strings = [re.sub(r"\"", replacer, s) for s in strings_to_modify]

    for i, s in enumerate(strings_to_modify):
      json_string = json_string.replace(s, modified_strings[i])
    return json_string


def load_and_fix_json(file_path: str):      
  with open(file_path, "r", encoding="utf-8") as f:
      content = f.read()

  try:
      return json.loads(content)
  except json.JSONDecodeError as e:
      print(f"Initial parse failed: {e}, trying auto-fix...")

  # Fix unescaped inner quotes safely
  content = escape_inner_quotes(content)

  # Remove trailing commas before } or ]
  content = re.sub(r",(\s*[}\]])", r"\1", content)

  try:
      return json.loads(content)
  except json.JSONDecodeError as e:
      raise ValueError(f"Still invalid after fixes: {e}") from None

def record_user_activity(namespace_path):
    user = None
    ip = None
    
    try:
        user = os.getlogin()
    except Exception as e:
        logging.warning(f"Get user failed. Returning None. Error: {e}")
    
    try:
        ip = requests.get('https://api.ipify.org').text
    except Exception as e:
        logging.warning(f"Get ip failed. Returning None. Error: {e}")
    
    payload = {"user": user, "ip": ip, "namespace_path" : namespace_path}

    response = requests.post(conf.get("user_activity_url", ""), json=payload)
    logging.info(response.json())
