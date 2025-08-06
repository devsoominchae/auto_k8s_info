#pod_info.py
import os
import json
import re

class PodInfo:
    def __init__(self, name, status, namespace_path):
        self.name = name
        self.status = status
        self.namespace_path = namespace_path
        self.errors = {}
        self.logs = []
        self.seen_messages = set()  # For filtering duplicates
        
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

    #seems a bit redundant right now... will fix later - has issues with timestamp comparison...
    def add_error_once_by_message(self, filename, category, line):
        try:
            # Try to load the full line as JSON directly
            log_json = json.loads(line.strip())
            message = log_json.get("message", log_json.get("messageKey", line.strip()))

            if message not in self.seen_messages:
                self.seen_messages.add(message)
                timestamp = log_json.get("timeStamp", "unknown-time")
                formatted = f"[{category}] {timestamp} - {message}"
                self.add_error(filename, formatted)

        except json.JSONDecodeError:
            # Not JSON – fallback
            if line not in self.seen_messages:
                self.seen_messages.add(line)
                self.add_error(filename, f"[{category}] {line.strip()}")


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
