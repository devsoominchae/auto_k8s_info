#main.py

import sys
sys.dont_write_bytecode = True

import os
import json
import re

from pod_info import PodInfo

with open('conf.json', 'r', encoding='utf-8') as f:
    conf = json.load(f)

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
    logs_dir = os.path.join(namespace_path, "logs")
    if not os.path.exists(logs_dir):
        print(f"No logs folder found at {logs_dir}")
        return

    for pod in pods_with_errors:
        print(f"\n=== Checking logs for pod: {pod.name} ===")
        pod.get_log_files()

        if not pod.logs:
            print(f"No log files found for pod {pod.name}")
            continue

        for file_name in pod.logs:
            log_file_path = os.path.join(logs_dir, file_name)
            print(f"Processing log file: {file_name}")

            with open(log_file_path, "r", encoding="utf-8", errors="ignore") as log_file:
                for line in log_file:
                    for category, patterns in conf['log_error_patterns'].items():
                        if any(p in line for p in patterns):
                            pod.add_error_once_by_message(file_name, category, line)
                            break

def main():
    if not os.path.exists(conf["cache"]):
        print(f'{conf["cache"]} does not exist. Creating a new one.')        
        with open('cache.json', 'w', encoding='utf-8') as f:
            json.dump(conf["cache_default"], f, indent=2)

    saved_case_info_dir = ""

    if os.path.exists(conf["cache"]):
        with open(conf["cache"], 'r') as cache_file:
            cache = json.load(cache_file)
            saved_case_info_dir = cache['saved_case_info_dir']

    if saved_case_info_dir:
        print(f"Saved path to get-k8s-info output: {saved_case_info_dir}")
        use_saved_path = input("Do you want to use this saved path? (yes - default/no): ").strip().lower()
        if use_saved_path not in conf["yes_list"]:
            saved_case_info_dir = ""
            case_info_dir = input("Please enter the path to the get-k8s-info output folder: ")
            cache['saved_case_info_dir'] = case_info_dir
            with open(conf["cache"], 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
        else:
            case_info_dir = saved_case_info_dir
            print(f"Using saved path: {case_info_dir}")
    else:
        case_info_dir = input("Please enter the path to the get-k8s-info output file: ")
        cache['saved_case_info_dir'] = case_info_dir
        with open(conf["cache"], 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)

    kubernetes_path = os.path.join(case_info_dir, 'kubernetes')
    if not os.path.exists(kubernetes_path):
        print(f"The 'kubernetes' folder does not exist under {case_info_dir}.")
        return

    folders = [f for f in os.listdir(kubernetes_path) if os.path.isdir(os.path.join(kubernetes_path, f))]
    if not folders:
        print("No folders found under 'kubernetes'.")
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

    get_pods_output = os.path.join(namespace_path, 'get','pods.txt')
    if not os.path.exists(get_pods_output):
        print(f"The file {get_pods_output} does not exist.")
        return

    with open(get_pods_output, 'r') as get_pods_output_file:
        get_pods_output_lines = get_pods_output_file.readlines()

    pods_with_errors = []
    for line in get_pods_output_lines:
        matched, category = line_matches_error_patterns(line, conf["get_pods_error_patterns"], "all")
        if matched:
            pod_name = line.split()[0]
            pod_info = PodInfo(pod_name, category, namespace_path)
            pod_info.add_error(get_pods_output, line.strip())
            pods_with_errors.append(pod_info)

    describe_pods_output = os.path.join(namespace_path, 'describe', 'pods.txt')
    if os.path.exists(describe_pods_output):
        with open(describe_pods_output, 'r') as describe_file:
            describe_lines = describe_file.readlines()
        pods_with_errors_name_list = [pod.name for pod in pods_with_errors]

        current_pod_name = None
        for line in describe_lines:
            if line.startswith('Name:'):
                current_pod_name = line.split()[1]
            if current_pod_name in pods_with_errors_name_list:
                matched, category = line_matches_error_patterns(line, conf["describe_pods_error_patterns"])
                if matched:
                    for pod in pods_with_errors:
                        if pod.name == current_pod_name:
                            pod.add_error(describe_pods_output, line.strip())
                            break

    log_file_collection(namespace_path, pods_with_errors)

    if pods_with_errors:
        print("Pods with errors:")
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

if __name__ == "__main__":
    main()
