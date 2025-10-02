#pod_info.py
import re
import os
import json

# Custom imports
from utils import logging, pluralize
from printer import Printer
from cleaner import clean_log, normalize_logs
from error_message import format_timestamp, parse_non_json_logs, get_full_error_message


class PodInfo:
    def __init__(self, name, status, node, namespace_path, printer):
        self.name = name
        self.status = status
        self.node = node
        self.namespace_path = namespace_path
        self.errors = {}
        self.logs = []
        self.seen_messages = {}
        self.printer = printer
        self.get_log_files()
        
    #extracts JSON messages from log lines, unless it fails
    def parse_json_message(self, line: str, category: str) -> str:
        try:
            # Extract JSON part (everything after "[Category] ")
            match = re.search(rf"\[{re.escape(category)}\]\s+(.*)", line.strip())
            if not match:
                return f"[{category}] {line.strip()}"

            json_part = match.group(1)
            log_json = json.loads(json_part)
            # Extract timestamp and message
            timestamp = log_json.get("timeStamp", "unknown-time")
            message = log_json.get("message", log_json.get("messageKey", "no-message"))

            return f"[{category}] {timestamp} - {message}"

        except Exception as e:
            print(f"[parse_json_message] Error: {e}")
            return f"[{category}] {line.strip()}"


    def add_error(self, filename, error):
        if filename not in self.errors:
            self.errors[filename] = []
        self.errors[filename].append(error)

    def add_error_once_by_message(self, filename, category, line, line_number):
        try:
            log_json = json.loads(line.strip())
            raw_message = get_full_error_message(line)
            timestamp = log_json.get("timeStamp", "unknown-time")
        except json.JSONDecodeError:
            timestamp, raw_message = parse_non_json_logs(line.strip())

        # normalize
        cleaned = clean_log(raw_message)
        dedup_key = normalize_logs(cleaned)  # strips timestamp/dynamic parts

        # prints timestamp
        formatted_error = f"{line_number}: [{category}] {format_timestamp(timestamp)} - {cleaned}"

        existing = self.seen_messages.get(dedup_key)

        # If timestamp is new it is changed
        if not existing or timestamp > existing[0]:
            self.seen_messages[dedup_key] = (timestamp, formatted_error)

        # Always rebuild the file's error list from seen_messages
        self.errors[filename] = [entry[1] for entry in self.seen_messages.values()]


    def print_info(self):
        self.printer.print_message("-" * 20)
        self.printer.print_message(f"Pod Name: {self.name}")
        self.printer.print_message(f"Status: {self.status}")
        self.printer.print_message(f"Node: {self.node}")
        self.printer.print_message(f"Log Files:")
        for log in self.logs:
            self.printer.print_message(f"- {log}")
        self.printer.print_message("\nDetails:")
        if self.errors:
            for filename, errors in self.errors.items():
                self.printer.print_message(f"\n{pluralize(len(errors), 'Issue')} in {filename}:")
                for error in errors:
                    self.printer.print_message(f"  - {error}")
        else:
            self.printer.print_message("No additional details available.")

        self.printer.print_message("-" * 20)
    
    def get_log_files(self):
        self.pod_logs_files_path = os.path.join(self.namespace_path, 'logs')
        if os.path.exists(self.pod_logs_files_path):
            self.logs = [os.path.join(self.pod_logs_files_path, f) for f in os.listdir(self.pod_logs_files_path) if f.startswith(self.name)]
        else:
            print(f"No logs directory found for {self.name} at {self.pod_logs_files_path}.\n")
    
    def print_pod_name(self):
        print(self.name)
    
    def get_pod_name(self):
        return self.name
    
    def print_logs(self):
        self.printer.print_message(f"Log files for {self.name}:")
        for log_file in self.logs:
            self.printer.print_message(f"- {log_file}")
    