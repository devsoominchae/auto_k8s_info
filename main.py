# main.py

import sys
sys.dont_write_bytecode = True

import os
import json

from pod_info import PodInfo, PodInfoDetail

K8S_ERROR = ["Error"]
K8S_RUNNING_NO_PODS = ["0/", "Running"]
K8S_INIT_HANG = ["Init:"]
K8S_CRASHED = ["CrashLoopBackOff"]

CONF = "conf.json"

# Function to check if a line contains all specified error strings listed in the constants
def contains_all_errors(line, error_strings):
    return all(error in line for error in error_strings)

def main():
    # Check if conf.json exists using the relataive path to where this script is located
    if not os.path.exists(CONF):
        print(f"{CONF} does not exist. Please create it with the required configurations.")
        return

    saved_k8s_file_path = ""

    # Load saved_k8s_file_path from conf.json if it exists
    if os.path.exists(CONF):
        with open(CONF, 'r') as conf_file:
            conf_data = json.load(conf_file)
            saved_k8s_file_path = conf_data.get('saved_k8s_file_path', None)

    # Show the saved path if it exists and ask if the user wants to use it
    if saved_k8s_file_path:
        print(f"Saved path to get-k8s-info output: {saved_k8s_file_path}")
        use_saved_path = input("Do you want to use this saved path? (yes/no): ").strip().lower()
        if use_saved_path != 'yes':
            saved_k8s_file_path = ""
            k8s_file_path = input(f"Please enter the path to the get-k8s-info output file: ")
            conf_data['saved_k8s_file_path'] = k8s_file_path
        
            # Replace the saved_k8s_file_path in conf.json
            with open(CONF, 'w', encoding='utf-8') as f:
                json.dump(conf_data, f, indent=2)
        else:
            k8s_file_path = saved_k8s_file_path
            print(f"Using saved path: {k8s_file_path}")

    else:
        # Get user input to specify the path to the get-k8s-info output
        k8s_file_path = input(f"Please enter the path to the get-k8s-info output file: ")
        conf_data['saved_k8s_file_path'] = k8s_file_path

        # Replace the saved_k8s_file_path in conf.json
        with open(CONF, 'w', encoding='utf-8') as f:
            json.dump(conf_data, f, indent=2)

    # List the folders under kubernetes folder and let user select one
    print("Available folders under kubernetes:")
    kubernetes_path = os.path.join(k8s_file_path, 'kubernetes')

    if not os.path.exists(kubernetes_path):
        print("The 'kubernetes' folder does not exist.")
        return
    
    folders = [f for f in os.listdir(kubernetes_path) if os.path.isdir(os.path.join(kubernetes_path, f))]

    if not folders:
        print("No folders found under 'kubernetes'.")
        return
    
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
        if (contains_all_errors(line, K8S_ERROR) or
            contains_all_errors(line, K8S_RUNNING_NO_PODS) or
            contains_all_errors(line, K8S_INIT_HANG) or
            contains_all_errors(line, K8S_CRASHED)):
            pod_name = line.split()[0]
            pod_status = f"{line.split()[1]} {line.split()[2]}"
            pod_info = PodInfo(pod_name, pod_status, namespace_path)

            pod_detail = PodInfoDetail(namespace_path)
            pod_detail.add_error(line.strip())
            pod_info.add_detail(pod_detail)

            pods_with_errors.append(pod_info)

    # Print the pods with errors
    if pods_with_errors:
        print("Pods with errors:")
        for pod in pods_with_errors:
            pod.print_info()

    else:
        print("No pods with errors found.")


# Test the main function
if __name__ == "__main__":
    main()