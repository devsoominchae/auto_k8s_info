# pod_info.py

import os

# Custom imports
from logging_conf import logging
from printer import Printer

class PodInfo:
    def __init__(self, name, status, node, namespace_path):
        self.name = name
        self.status = status
        self.node = node
        self.namespace_path = namespace_path
        self.errors = {}
        self.logs = []
        self.logged_categories = set()
        self.printer = Printer(os.path.basename(namespace_path), mode="both")

    def add_error(self, filename, error):
        if filename not in self.errors:
            self.errors[filename] = []
        self.errors[filename].append(error)
        logging.info(f"Error in {filename}: {error}")

        
    def add_error_once(self, filename, category, line): # TODO: Discuss if there is a better name for this function
            #Removes duplicate when outputting to json file
            if category in self.logged_categories:
                return
            self.add_error(filename, f"[{category}] {line.strip()}")
            self.logged_categories.add(category)
            logging.info(f"Error in {filename} [{category}]: {line.strip()}")
            
    def print_info(self):
        self.printer.print_message("-" * 20)
        self.printer.print_message(f"Pod Name: {self.name}")
        self.printer.print_message(f"Status: {self.status}")
        self.printer.print_message(f"Node: {self.node}")
        self.printer.print_message("Details:")
        if self.errors:
            for filename, errors in self.errors.items():
                self.printer.print_message(f"\nIssues in {filename}:")
                for error in errors:
                    self.printer.print_message(f"  - {error}")
        else:
            self.printer.print_message("No additional details available.")
        
        self.get_log_files()

        self.printer.print_message("-" * 20)
    
    def get_log_files(self):
        self.pod_logs_files_path = os.path.join(self.namespace_path, 'logs')
        if os.path.exists(self.pod_logs_files_path):
            self.logs = [os.path.join(self.pod_logs_files_path, f) for f in os.listdir(self.pod_logs_files_path) if f.startswith(self.name)]
        else:
            print(f"No logs directory found for {self.name} at {self.pod_logs_files_path}.")
    
    def print_pod_name(self):
        print(self.name)
    
    def get_pod_name(self):
        return self.name
    
    def print_logs(self):
        self.printer.print_message(f"Log files for {self.name}:")
        for log_file in self.logs:
            self.printer.print_message(f"- {log_file}")
    