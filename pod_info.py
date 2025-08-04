# pod_info.py

import os

class PodInfo:
    def __init__(self, name, status, namespace_path):
        self.name = name
        self.status = status
        self.namespace_path = namespace_path
        self.errors = {}
        self.logs = []
        self.logged_categories = set() 

    def add_error(self, filename, error):
        if filename not in self.errors:
            self.errors[filename] = []
        self.errors[filename].append(error)
        
    def add_error_once(self, filename, category, line):
            #Removes duplicate when outputting to json file
            if category in self.logged_categories:
                return
            self.add_error(filename, f"[{category}] {line.strip()}")
            self.logged_categories.add(category)
            
    def print_info(self):
        print("-" * 20)
        print(f"Pod Name: {self.name}")
        print(f"Status: {self.status}")
        print("Details:")
        if self.errors:
            for filename, errors in self.errors.items():
                print(f"\nErrors in {filename}:")
                for error in errors:
                    print(f"  - {error}")
        else:
            print("No additional details available.")
        
        print("\nLogs:")
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
    