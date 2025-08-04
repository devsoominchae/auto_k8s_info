# main.py

import os
import json

from pod_info import PodInfo
import re


with open('conf.json', 'r', encoding='utf-8') as f:
    conf = json.load(f)

def remove_invalid_windows_chars(filename):
    invalid_chars = conf['invalid_windows_path_chars']
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename

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

# Function to check if a line contains all specified error strings listed in the constants
def contains_all_errors(line, error_strings):
    return all(error in line for error in error_strings)


def log_file_collection(namespace_path, pods_with_errors):
    logs_dir = os.path.join(namespace_path, "logs")

    if not os.path.exists(logs_dir):
        print(f"No logs folder found at {logs_dir}")
        return

    for pod in pods_with_errors:
        print(f"\n=== Checking logs for pod: {pod.name} ===")
        found_logs = False

        for file_name in os.listdir(logs_dir):
            if file_name.startswith(pod.name): 
                found_logs = True
                log_file_path = os.path.join(logs_dir, file_name)

                print(f"Processing log file: {file_name}")

                with open(log_file_path, "r", encoding="utf-8", errors="ignore") as log_file:
                    seen_categories = set()

                    for line in log_file:
                        matched, category = line_matches_error_patterns(line, conf['log_error_patterns'])
                        if matched:
                            if category not in seen_categories:
                                seen_categories.add(category)
                                pod.add_error(file_name, f"[{category}] {line.strip()}")


        if not found_logs:
            print(f"No log files found for pod {pod.name}")
            
        

def main():
    # Check if cache.json exists using the relataive path to where this script is located
    if not os.path.exists(conf["cache"]):
        print(f'{conf["cache"]} does not exist. Creating a new one.')        

        with open('cache.json', 'w', encoding='utf-8') as f:
            json.dump(conf["cache_default"], f, indent=2)

    saved_case_info_dir = ""

    # Load saved_case_info_dir from cache.json if it exists
    if os.path.exists(conf["cache"]):
        with open(conf["cache"], 'r') as cache_file:
            cache = json.load(cache_file)
            saved_case_info_dir = cache['saved_case_info_dir']

    # Show the saved path if it exists and ask if the user wants to use it
    if saved_case_info_dir:
        print(f"Saved path to get-k8s-info output: {saved_case_info_dir}")
        use_saved_path = remove_invalid_windows_chars(input("Do you want to use this saved path? (yes - default/no): ").strip().lower())

        if use_saved_path not in conf["yes_list"]:
            saved_case_info_dir = ""
            case_info_dir = remove_invalid_windows_chars(input(f"Please enter the path to the get-k8s-info output folder: ").strip())
            cache['saved_case_info_dir'] = case_info_dir
        
            # Replace the saved_case_info_dir in cache.json
            with open(conf["cache"], 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
        else:
            case_info_dir = saved_case_info_dir
            print(f"Using saved path: {case_info_dir}")

    else:
        # Get user input to specify the path to the get-k8s-info output
        case_info_dir = remove_invalid_windows_chars(input("Please enter the path to the get-k8s-info output file: ").strip())
        cache['saved_case_info_dir'] = case_info_dir

        # Replace the saved_case_info_dir in cache.json
        with open(conf["cache"], 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)

    # List the folders under kubernetes folder and let user select one
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

    folder_choice = input("Please select a folder by number: ")

    try:
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

    # Read the content of kubectl get pods command output
    get_pods_output = os.path.join(namespace_path, 'get','pods.txt')
    if not os.path.exists(get_pods_output):
        print(f"The file {get_pods_output} does not exist.")
        return
    
    with open(get_pods_output, 'r') as get_pods_output_file:
        get_pods_output_lines = get_pods_output_file.readlines()
    
    # Check each line in the pods content and save the pod names if it contains all strings in K8S_ERROR, K8S_RUNNING_NO_PODS, K8S_INIT_HANG, K8S_CRASHED
    pods_with_errors = []

    for line in get_pods_output_lines:
        matched, category = line_matches_error_patterns(line, conf["get_pods_error_patterns"], "all")
        if matched:
            pod_name = line.split()[0]
            pod_info = PodInfo(pod_name, category, namespace_path)
            pod_info.add_error(get_pods_output, line.strip())

            pods_with_errors.append(pod_info)

    
    # Read the kubectl describe pods command output
    describe_pods_output = os.path.join(namespace_path, 'describe', 'pods.txt')
    if not os.path.exists(describe_pods_output):
        print(f"The file {describe_pods_output} does not exist.")
    else:
        with open(describe_pods_output, 'r') as describe_pods_output_file:
            describe_pods_output_lines = describe_pods_output_file.readlines()
        # Check each line in the describe pods content and check if it contains the pod name in pods_with_errors
        pods_with_errors_name_list = [pod.name for pod in pods_with_errors]

        for line in describe_pods_output_lines:
            if line.startswith('Name:'):
                current_pod_name = line.split()[1]

            if current_pod_name in pods_with_errors_name_list and line_matches_error_patterns(line, conf["describe_pods_error_patterns"])[0]:
                for pod in pods_with_errors:
                    if pod.name == current_pod_name:
                        pod.add_error(describe_pods_output, line.strip())
                        break
                
    log_file_collection(namespace_path, pods_with_errors)

    # Print the pods with errors
    #Code to print onto a json, without the clutter
    if pods_with_errors:
        print("Pods with errors:")
        for pod in pods_with_errors:
            pod.print_info()

        all_errors_path = os.path.join(namespace_path, "all_errors.json")
        clean_errors_output = {}

        for pod in pods_with_errors:
            flat_errors = []  # a single list for this pod
            for messages in pod.errors.values():  # loop through all error lists from all files
                flat_errors.extend(messages)  # add them into one cleaned list
            clean_errors_output[pod.name] = flat_errors  # store only pod name and messages

        with open(all_errors_path, "w", encoding="utf-8") as f:
            json.dump(clean_errors_output, f, indent=2)

        print(f"\n Clean errors saved to: {all_errors_path}")


# Test the main function
if __name__ == "__main__":
    main()
    
