# main.py
import os
import json
import re

# Custom imports
from utils import conf, load_cache, get_case_info_dir_from_user, logging
from printer import Printer
from pod_info import PodInfo

from mongodb_handler import MongoHandler
from dotenv import load_dotenv
import os



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

# Collect log file errors for each pod
# If a log line matches a pattern, we parse it and store only unique messages ignoring timestamp
def log_file_collection(namespace_path, pods_with_errors):
    printer = Printer(os.path.basename(namespace_path), mode="console")
    logs_dir = os.path.join(namespace_path, "logs")
    if not os.path.exists(logs_dir):
        printer.print_message(f"No logs folder found at {logs_dir}")
        logging.warning(f"No logs folder found at {logs_dir}. Skipping log file collection.")
        return

    for pod in pods_with_errors:
        printer.print_message(f"\n=== Checking logs for pod: {pod.name} ===", print_level=2)
        pod.get_log_files()

        if not pod.logs:
            printer.print_message(f"No log files found for pod {pod.name}")
            continue

        for file_name in pod.logs:
            log_file_path = os.path.join(logs_dir, file_name)
            printer.print_message(f"Processing log file: {file_name}", print_level=2)

            with open(log_file_path, "r", encoding="utf-8", errors="ignore") as log_file:
                for line in log_file:
                    for category, patterns in conf.get('log_error_patterns', {}).items():
                        if any(p in line for p in patterns):
                            pod.add_error_once_by_message(file_name, category, line)
                            break

def main():
    # Check if cache.json exists using the relataive path to where this script is located
    logging.info("START")
    
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI")

    if not mongo_uri:
        print("MongoDB URI not found in environment variables. Exiting.")
        return

    mongo = MongoHandler(uri=mongo_uri)

    # Replace conf log_error_patterns with patterns from MongoDB
    conf["log_error_patterns"] = mongo.get_error_patterns()
    cache = load_cache()

    case_info_dir = get_case_info_dir_from_user(cache)

    # List the folders under kubernetes folder and let user select one
    kubernetes_path = os.path.join(case_info_dir, 'kubernetes')
    if not os.path.exists(kubernetes_path):
        print(f"The 'kubernetes' folder does not exist under {case_info_dir}.")
        logging.error(f"The 'kubernetes' folder does not exist under {case_info_dir}. Exiting the program.")
        return

    folders = [f for f in os.listdir(kubernetes_path) if os.path.isdir(os.path.join(kubernetes_path, f))]
    if not folders:
        print("No folders found under 'kubernetes'.")
        logging.error("No folders found under 'kubernetes'. Exiting the program.")
        return

    print("Available folders under kubernetes:")
    for idx, folder in enumerate(folders):
        print(f"{idx + 1}: {folder}")

    try:
        folder_choice = input("Please select a folder by number: ")
        folder_index = int(folder_choice) - 1
        if folder_index < 0 or folder_index >= len(folders):
            print("Invalid selection.")
            return
        selected_folder = folders[folder_index]
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    print(f"You selected: {selected_folder}\n")
    namespace_path = os.path.join(kubernetes_path, selected_folder)
    logging.info(f"Processing logs on {namespace_path}")

    get_pods_output = os.path.join(namespace_path, 'get','pods.txt')
    if not os.path.exists(get_pods_output):
        print(f"The file {get_pods_output} does not exist.")
        logging.error(f"The file {get_pods_output} does not exist. Exiting the program.")
        return

    with open(get_pods_output, 'r') as get_pods_output_file:
        get_pods_output_lines = get_pods_output_file.readlines()

    if 'NODE' in get_pods_output_lines[0]:
        node_name_index = get_pods_output_lines[0].split().index('NODE')
        fields = get_pods_output_lines[0].split()
        node_name_index = fields.index('NODE')
        reverse_node_name_index = -(len(fields) - 2 - node_name_index)
    else:
        print("The 'NODE' column is not present in the get pods output. Defaulting to 'unknown'.")
        logging.warning("The 'NODE' column is not present in the get pods output. Defaulting to 'unknown'.")

    pods_with_errors = []
    pods_without_errors = []

    for line in get_pods_output_lines:
        matched, category = line_matches_error_patterns(line, conf.get("get_pods_error_patterns", {}), "all")
        pod_name = line.split()[0]
        pod_node = line.split()[reverse_node_name_index] if reverse_node_name_index != -1 else "unknown"
        if matched:
            pod_info = PodInfo(pod_name, category, pod_node, namespace_path)
            pod_info.add_error(get_pods_output, line.strip())
            pods_with_errors.append(pod_info)
        elif not matched and pod_name != "NAME":
            pod_info = PodInfo(pod_name, "No Issues", pod_node, namespace_path)
            pods_without_errors.append(pod_info)

    
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
        for line in describe_pods_output_lines:
            if line.startswith('Name:'):
                current_pod_name = line.split()[1]
            if current_pod_name in pods_with_errors_name_list:
                matched, category = line_matches_error_patterns(line, conf.get("describe_pods_error_patterns", {}))
                if matched:
                    for pod in pods_with_errors:
                        if pod.name == current_pod_name:
                            pod.add_error(describe_pods_output, line.strip())
                            break

    log_file_collection(namespace_path, pods_with_errors)

    if pods_with_errors:
        print("\nPods with issues:")
        logging.info(f"Found {len(pods_with_errors)} pods with issues:")
        for pod in pods_with_errors:
            print(f"- {pod.get_pod_name()}")
            logging.info(f"- {pod.get_pod_name()}")

    if pods_with_errors:
        print("\nDetails on pods with issues:")
        for pod in pods_with_errors:
            pod.print_info()

        all_errors_path = os.path.join(namespace_path, "all_errors.json")
        clean_errors_output = {}

        for pod in pods_with_errors:
            flat_errors = []
            for messages in pod.errors.values():
                flat_errors.extend(messages)
            clean_errors_output[pod.name] = flat_errors

        with open(all_errors_path, "w", encoding="utf-8") as f:
            json.dump(clean_errors_output, f, indent=2)

        print(f"\n Clean errors saved to: {all_errors_path}")
    
    # log_file_collection(namespace_path, pods_without_errors)

    # if pods_without_errors:
    #     print("\nPods without issues:")
    #     for pod in pods_without_errors:
    #         if pod.errors:
    #             pod.print_info()

if __name__ == "__main__":
    main()
