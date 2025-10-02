# utils.py

import re
import os
import json
import logging
import inflect
import requests
import datetime

# Custom imports



RESTORE_CONF_FILE = 'conf_restored.json'
CONF = {
    "cache": "cache.json",
    "cache_default": {
        "saved_case_info_dir": "",
        "error_patterns": ""
    },
    "restart_filter_threshold": {
        "default": 3,
        "sas-workload-orchestrator": 1,
        "sas-analytics-execution": 2
    },
    "max_files_to_show": 10,
    "mongodb_conn_var_url": "http://trck1076843.trc.sas.com:8000/.env",
    "user_activity_url": "http://trck1076843.trc.sas.com:8000/record",
    "output_timestamp_format": "%Y-%m-%d %H:%M:%S",
    "print_level": 1,
    "output_folder": "output",
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s %(levelname)s %(message)s",
        "retention_days": 1,
        "file_name": "auto_k8s_info.log"
    },
    "cleaner": {
        "ip_address": True,
        "port": True,
        "job_number": True
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
            "OOMKilled",
            "OutOfcpu",
            "Error"
        ],
        "Pod rejected": [
            "Pod was rejected: Node didn't have enough resource:"
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
        "Out of CPU": [
            "OutOfcpu"
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
            "cas-control is not ready",
            "Unable to lookup CAS server cas-gp-default.  Response code 404 received",
            "Deleting failed ControllerPod"
        ],
        "CAS Worker Issues": [
            "TKCASTAB_GENERIC_TKIOE_FAIL"
        ],
        "Start Sequencer Warnings": [
            "SKIP_INIT_BLOCK",
            "bypassing sequencing"
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
        "Authentication Failures": [
            "Unauthorized",
            "authentication failed",
            "access denied",
            "invalid credentials",
            "token expired",
            "password authentication failed"
        ],
        "Tool Execution Failures": [
            "sonder-log-icu.tool.error.executing.command.log",
            "sonder-log-icu.tool.executor.failed.running.tools.log",
            "Service executor failed to execute successfully: exit status 1"
        ],
        "Certificate Write Failures": [
            "writeAsPem failed",
            "error writing PEM file",
            "failed to decode pem block"
        ],
        "Certificate Errors": [
            "CA certificate Secret already exists",
            "error generating certificates",
            "failed to create cert secret",
            "failed to write certificate file",
            "invalid certificate configuration"
        ],
        "PVC Errors": [
            "PersistentVolumeClaim is not bound",
            "PersistentVolumeClaim is not available",
            "PersistentVolumeClaim is in pending state",
            "PVC pending"
        ],
        "FailedMount Errors": [
            "MountVolume.SetUp failed for volume",
            "references non-existent secret key"
        ],
        "Compute Context Errors": [
            "Compute context to be used by the CAS Formats service",
            "no ready CAS servers, so cas-control is not ready"
        ],
        "Timeouts": [
            "Request timed out",
            "Connection timed out"
        ],
        "PyConfig errors": [
            "Error creating md5sum file"
        ],
        "SAS ESP CSS Errors": [
            "could not find a valid ESP SERVER license"
        ],
        "Bootstrap Errors": [
            "Error bootstrapping resources:",
            "The bootstrap request failed:"
        ],
        "JSON Errors": [
            "JSONDecodeError"
        ],
        "Token Errors": [
            "Failed to obtain dedicated tokens"
        ],
        "Security Constraint Errors": [
            "is forbidden: unable to validate against any security context constraint"
        ],
        "Consul issues": [
            "No cluster leader"
        ],
        "TLS Handshake errors": [
            "http: TLS handshake timeout"
        ],
        "RabbitMQ issues": [
            "Error on AMQP connection",
            "reason: {{badmatch,{error,noproc}},",
            "reason: reached_max_restart_intensity",
            "errorContext: child_terminated",
            "errorContext: shutdown"
        ],
        "Workload Orchestrator issues": [
            "SGMGM_MSG_MANAGER_JOB_KILLED"
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
        logging.FileHandler(conf.get('logging', {}).get('file_name', "auto_k8s_info.log"), encoding='utf-8')  # Log to file
    ]
)

def manage_log_retention():   
    log_file_path = conf.get('logging', {}).get('file_name', "auto_k8s_info.log")
    retention_days = conf.get('logging', {}).get("retention_days", 7)

    # Calculate the cutoff date
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)

    # Read and filter log lines
    cutoff_date_passed = False
    filtered_lines = []
    if os.path.exists(log_file_path):
        with open(log_file_path, "r") as file:
            for line in file:
                try:
                    # Assuming log lines start with 'YYYY-MM-DD HH:MM:SS'
                    timestamp_str = line[:19]
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    if timestamp >= cutoff_date:
                        cutoff_date_passed = True
                    if cutoff_date_passed:
                        filtered_lines.append(line)
                except ValueError:
                    # Keep lines that don't start with a timestamp
                    if cutoff_date_passed:
                        filtered_lines.append(line)

    # Overwrite the log file with filtered lines
    with open(log_file_path, "w") as file:
        file.writelines(filtered_lines)

    formatted_cutoff_date = cutoff_date.strftime(conf.get("output_timestamp_format", "%Y-%m-%d %H:%M:%S"))
    
    print(f"Log file cleaned. Entries older than {pluralize(retention_days, 'day')}, before {formatted_cutoff_date}, have been removed.")
    logging.info(f"Log file cleaned. Entries older than {pluralize(retention_days, 'day')}, before {formatted_cutoff_date}, have been removed.")

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
    
    try:
        user = os.getlogin()
    except Exception as e:
        logging.warning(f"Get user failed. Returning None. Error: {e}")
    
    payload = {"user": user, "namespace_path" : namespace_path}

    response = requests.post(conf.get("user_activity_url", ""), json=payload)
    logging.info(f'Response from {conf.get("user_activity_url", "")}: {response}')
