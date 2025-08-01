# pod_info.py

import os
import re
import json

class PodInfo:
    def __init__(self, name, status, namespace_path):
        self.name = name
        self.status = status
        self.namespace_path = namespace_path
        self.details = []
        self.logs = []

    def add_detail(self, detail):
        self.details.append(detail)
    
    def print_info(self):
        print("-" * 20)
        print(f"Pod Name: {self.name}")
        print(f"Status: {self.status}")
        print("Details:")
        if self.details:
            for detail in self.details:
                detail.print_errors()
        else:
            print("No additional details available.")
        
        print("Logs:")
        self.get_log_files()

        if self.logs:
            self.print_logs()
        else:
            print("No log files available.")
        print("-" * 20)
    
    def get_log_files(self):
        self.pod_logs_files_path = os.path.join(self.namespace_path, 'logs')
        if os.path.exists(self.pod_logs_files_path):
            self.logs = [f for f in os.listdir(self.pod_logs_files_path) if f.startswith(self.name)]
        else:
            print(f"No logs directory found for {self.name} at {self.pod_logs_files_path}.")
    
    def print_logs(self):
        print(f"Log files for {self.name}:")
        for log_file in self.logs:
            print(f"- {log_file}")
    

class PodInfoDetail:
    def __init__(self, source_file_path):
        self.source_file_path = source_file_path
        self.errors = []
    
    def add_error(self, error):
        self.errors.append(error)
    
    def print_errors(self):
        if self.errors:
            print(f"Errors in {self.source_file_path}:")
            for error in self.errors:
                print(f"- {error}")
        else:
            print(f"No errors found in {self.source_file_path}.")