# error_info.py

import os
import sys
import json

# Custom imports
from utils import conf, logging, format_timestamp, parse_container_name, pluralize, parse_non_json_logs
from cleaner import clean_log
from printer import Printer
from pod_info import PodInfo

class ErrorInfo:
    def __init__(self, timestamp, message, category, container, file_name, line_number):
        self.timestamp = timestamp
        self.message = message
        self.category = category
        self.file_name = file_name
        self.line_number = line_number
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
    
    def format_error(self, line, file_name, category, line_number):
        message = ""
        timestamp = ""
        container = parse_container_name(file_name)
        try:
            # Try to load the full line as JSON directly
            log_json = json.loads(line.strip())
            message = clean_log(f'{log_json.get("message")} {log_json.get("messageKey", line.strip())}')
            timestamp = log_json.get("timeStamp") or log_json.get("ts") or "unknown-time"

        except json.JSONDecodeError:
                logging.info(f"The log snippet {line} is from {file_name} is not in JSON format. Returning original message")
                timestamp, message = parse_non_json_logs(line.strip())
        
        error_info = ErrorInfo(format_timestamp(timestamp), message, category, container, file_name, line_number)
        return error_info
    
    def print_pods_by_error_category(self):
        for category, error_infos in self.errors.items():
            self.printer.print_message(f"\nError: [{category}] found in {pluralize(len(error_infos), 'file')}")
            self.printer.print_message("List of files:")
            for error_info in error_infos[:conf["max_files_to_show"]]:
                if error_info.message:
                    self.printer.print_message(f" - {error_info.file_name} [{error_info.line_number}]: {error_info.message}")
            if len(error_infos) > conf["max_files_to_show"]:
                self.printer.print_message(f" - ... and {pluralize(len(error_infos) - conf['max_files_to_show'], 'more file')}\n")
    
    def print_containers_by_error_category(self):
        for category, error_infos in self.errors.items():
            containers_with_errors = set(error_info.container for error_info in error_infos)
            self.printer.print_message(f"\nError [{category}] found in {pluralize(len(containers_with_errors), 'container')}")
            for container in containers_with_errors:
                if container:
                    self.printer.print_message(f" - {container}")

# Collect log file errors for each pod
# If a log line matches a pattern, we parse it and store only unique messages ignoring timestamp
def analyze_pods_with_errors(namespace_path, pods_with_errors, printer, error_patterns):
    logs_dir = os.path.join(namespace_path, "logs")
    if not os.path.exists(logs_dir):
        printer.print_message(f"No logs folder found at {logs_dir}")
        logging.warning(f"No logs folder found at {logs_dir}. Skipping log file collection.")
        return

    for pod in pods_with_errors:
        printer.print_message(f"\n=== Checking logs for pod: {pod.name} ===", print_level=2)

        if not pod.logs:
            printer.print_message(f"No log files found for pod {pod.name}")
            continue

        for file_name in pod.logs:
            log_file_path = os.path.join(logs_dir, file_name)
            printer.print_message(f"Processing log file: {file_name}", print_level=2)

            with open(log_file_path, "r", encoding="utf-8", errors="ignore") as log_file:
                for line_number, line in enumerate(log_file, start=1):
                    for category, patterns in error_patterns.items():
                        if any(p in line for p in patterns):
                            pod.add_error_once_by_message(file_name, category, line, line_number)
                            break
                    
                # pod.add_error_once_by_message(file_name, "Most Recent Record", log_file[-1].strip())

def analyze_pods_without_errors(namespace_path, pods_without_errors, printer, error_patterns):
    error_info_holder = ErrorInfoHolder(printer)
    printer_console = Printer(namespace_path, mode="console")
    printer.print_message("\nAnalyzing pods in normal state.")

    i = 0
    total_number_of_log_files = sum(len(pod.logs) for pod in pods_without_errors)

    for pod in pods_without_errors:
        printer.print_message(f"\n=== Analyzing pod without errors: {pod.name} ===", print_level=2)

        if not pod.logs:
            printer.print_message(f"No log files found for pod {pod.name}\n")
            continue

        for file_name in pod.logs:
            i += 1
            sys.stdout.write("\033[K")
            printer_console.print_message(f"[{i}/{total_number_of_log_files} {i/total_number_of_log_files*100:.1f}%] Processing log file: {os.path.basename(file_name)}", print_level=1, end_="\r", flush_=True)
            if file_name.endswith("sas-rabbitmq-server-0_sas-start-sequencer.log"):
                pass
            with open(file_name, "r", encoding="utf-8", errors="ignore") as log_file:
                for line_number, line in enumerate(log_file, start=1):
                    for category, patterns in error_patterns.items():
                        if any(p in line for p in patterns):
                            error_info = error_info_holder.format_error(line, file_name, category, line_number)
                            error_info_holder.add_error(error_info)

    return error_info_holder

def line_matches_error_patterns(line, error_patterns, mode='any'):
    result = False, None
    for category, patterns in error_patterns.items():
        if mode == 'any':
            if any(p in line for p in patterns):
                result = True, category
                break
        elif mode == 'all':
            if all(p in line for p in patterns):
                result = True, category
                break
    return result

def analyze_describe_pods_output(namespace_path, pods_with_errors):
    # Read the kubectl describe pods command output
    describe_pods_output = os.path.join(namespace_path, 'describe', 'pods.txt')
    if not os.path.exists(describe_pods_output):
        print(f"The file {describe_pods_output} does not exist.")
        logging.warning(f"The file {describe_pods_output} does not exist. Skipping error checks in describe pods output.")
    else:
        with open(describe_pods_output, 'r') as describe_pods_output_file:
            describe_pods_output_lines = describe_pods_output_file.readlines()
        # Check each line in the describe pods content and check if it contains the pod name in pods_with_errors
        pods_with_errors_name_list = [pod.name for pod in pods_with_errors]

        current_pod_name = None
        for line_number, line in enumerate(describe_pods_output_lines, start=1):
            if line.startswith('Name:'):
                current_pod_name = line.split()[1]
            if current_pod_name in pods_with_errors_name_list:
                matched, category = line_matches_error_patterns(line, conf.get("describe_pods_error_patterns", {}))
                if matched:
                    for pod in pods_with_errors:
                        if pod.name == current_pod_name:
                            pod.add_error(describe_pods_output, f"{line_number}: {clean_log(line.strip())}")
                            break
    return pods_with_errors

def classify_pods(namespace_path, printer):
    column_index = 0
    reverse_node_name_index = 0 
    get_pods_output = os.path.join(namespace_path, 'get','pods.txt')
    if not os.path.exists(get_pods_output):
        print(f"The file {get_pods_output} does not exist.")
        logging.error(f"The file {get_pods_output} does not exist. Exiting the program.")
        return

    with open(get_pods_output, 'r') as get_pods_output_file:
        get_pods_output_lines = get_pods_output_file.readlines()

    for i, line in enumerate(get_pods_output_lines):
        if line.startswith("NAME"):
            column_index = i
            break

    if 'NODE' in get_pods_output_lines[column_index]:
        node_name_index = get_pods_output_lines[column_index].split().index('NODE')
        fields = get_pods_output_lines[column_index].split()
        node_name_index = fields.index('NODE')
        reverse_node_name_index = -(len(fields) - 2 - node_name_index)
    else:
        print("The 'NODE' column is not present in the get pods output. Defaulting to 'unknown'.")
        logging.warning("The 'NODE' column is not present in the get pods output. Defaulting to 'unknown'.")

    pods_with_errors = []
    pods_without_errors = []

    for line_number, line in enumerate(get_pods_output_lines[column_index + 1:], start=column_index + 2):
        matched, category = line_matches_error_patterns(line, conf.get("get_pods_error_patterns", {}), "all")
        line_list = line.split()
        pod_name = line_list[0]
        pod_node = line_list[reverse_node_name_index] if reverse_node_name_index != -1 else "unknown"
        
        pod_restarts = int(line_list[3])
        pod_restart_filter_threshold = get_pod_restart_filter_threshold(pod_name)
        if pod_restarts > pod_restart_filter_threshold:
            category = f'Restart threshold({pod_restart_filter_threshold}) exceeded'
            matched = True
            
        if matched:
            pod_info = PodInfo(pod_name, category, pod_node, namespace_path, printer)
            pod_info.add_error(get_pods_output, f"{line_number}: {line.strip()}")
            pods_with_errors.append(pod_info)
        elif not matched and pod_name != "NAME":
            pod_info = PodInfo(pod_name, "No Issues", pod_node, namespace_path, printer)
            pods_without_errors.append(pod_info)
        
    return pods_with_errors, pods_without_errors

def get_pod_restart_filter_threshold(pod_name):
    for pod_name_key, threshold in conf.get("restart_filter_threshold", {}).items():
        if pod_name.startswith(pod_name_key):
            return threshold
    return conf.get("restart_filter_threshold", {}).get("default", 10)