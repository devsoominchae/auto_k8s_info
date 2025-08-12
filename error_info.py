# error_info.py

import os
import json

# Custom imports
from utils import conf, logging, format_timestamp, parse_container_name
from printer import Printer

class ErrorInfo:
    def __init__(self, timestamp, message, category, container, file_name):
        self.timestamp = timestamp
        self.message = message
        self.category = category
        self.file_name = file_name
        self.container = container


class ErrorInfoHolder:
    def __init__(self, printer):
        self.errors = {}
        self.added_files = set()
        self.printer = printer
        
    
    def add_error(self, error_info):
        if error_info.category not in self.errors:
            self.errors[error_info.category] = []

        if f"{error_info.file_name}_{error_info.category}" not in self.added_files:
            self.added_files.add(f"{error_info.file_name}_{error_info.category}")
            self.errors[error_info.category].append(error_info)
    
    def format_error(self, line, file_name, category):
        message = ""
        timestamp = ""
        container = ""
        try:
            # Try to load the full line as JSON directly
            log_json = json.loads(line.strip())
            message = log_json.get("message", log_json.get("messageKey", line.strip()))
            timestamp = log_json.get("timeStamp", "unknown-time")
            container = parse_container_name(file_name)

        except json.JSONDecodeError:
                logging.info(f"The log snippet {line} is from {file_name} is not in JSON format. Returning original message")
        
        error_info = ErrorInfo(format_timestamp(timestamp), message, category, container, file_name)
        return error_info
    
    def print_pods_by_error_category(self):
        for category, error_infos in self.errors.items():
            self.printer.print_message(f"Error: [{category}] found in {len(error_infos)} files")
            self.printer.print_message("List of files:")
            for error_info in error_infos[:conf["max_files_to_show"]]:
                if error_info.message:
                    self.printer.print_message(f" - {os.path.basename(error_info.file_name)} : {error_info.message}")
            if len(error_infos) > conf["max_files_to_show"]:
                self.printer.print_message(f" - ... and {len(error_infos) - conf['max_files_to_show']} more files\n")
    
    def print_containers_by_error_category(self):
        for category, error_infos in self.errors.items():
            containers_with_errors = set(error_info.container for error_info in error_infos)
            self.printer.print_message(f"\nError [{category}] found in {len(containers_with_errors)} containers")
            for container in containers_with_errors:
                if container:
                    self.printer.print_message(f" - {container}")