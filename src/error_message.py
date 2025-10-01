import json

from thefuzz import fuzz

from utils import conf, logging

def format_timestamp(timestamp):
    """Format a timestamp string to a more readable format."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime(conf.get("output_timestamp_format", "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        logging.info(f"Invalid timestamp format: {timestamp}. Using original.")
        return timestamp

def parse_non_json_logs(line):
    timestamp = line.split()[0]
    error = " ".join(line.split()[1:])
    return timestamp, error

def get_full_error_message(line):
    log_json = json.loads(line.strip())
    
    message = log_json.get("message", "")
    message_key = log_json.get("messageKey", "")
    
    if not message and not message_key:
        return line
    
    return check_message_duplicate(message, message_key)

def check_message_duplicate(message, message_key):
    if any(
        [fuzz.ratio(message, message_key) >= 80,
        message in message_key,
        message_key in message]
    ):
        return message if len(message) >= len(message_key) else message_key
    return f"{message} | {message_key}"