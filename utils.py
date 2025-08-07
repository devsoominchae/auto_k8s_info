# utils.py

import os
import json

with open('conf.json', 'r', encoding='utf-8') as f:
    conf = json.load(f)


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
