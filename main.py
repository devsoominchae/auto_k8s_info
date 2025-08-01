# main.py

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

    # Get user input to specify the path to the get-k8s-info output
    k8s_file_path = input(f"Please enter the path to the get-k8s-info output file: {saved_k8s_file_path}")

    # If the user did not provide a path, use the saved path from conf.json
    if not k8s_file_path:
        k8s_file_path = saved_k8s_file_path

    # If the user provided a path, save it to conf.json
    if k8s_file_path:
        with open(CONF, 'w') as conf_file:
            json.dump({'saved_k8s_file_path': k8s_file_path}, conf_file)

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

    # Read the content of kubectl get pods command output
    pods_file_path = os.path.join(kubernetes_path, selected_folder, 'get','pods.txt')
    if not os.path.exists(pods_file_path):
        print(f"The file {pods_file_path} does not exist.")
        return
    
    with open(pods_file_path, 'r') as pods_file:
        pods_content_lines = pods_file.readlines()
    
    # Check each line in the pods content and save the pod names if it contains all strings in K8S_ERROR, K8S_RUNNING_NO_PODS, K8S_INIT_HANG, K8S_CRASHED
    pods_with_errors = []
    for line in pods_content_lines:
        if (contains_all_errors(line, K8S_ERROR) or
            contains_all_errors(line, K8S_RUNNING_NO_PODS) or
            contains_all_errors(line, K8S_INIT_HANG) or
            contains_all_errors(line, K8S_CRASHED)):
            pod_name = line.split()[0]
            pod_status = f"{line.split()[1]} {line.split()[2]}"
            pod_info = PodInfo(pod_name, pod_status, os.path.join(kubernetes_path, selected_folder))

            pod_detail = PodInfoDetail(pods_file_path)
            pod_detail.add_error(line.strip())
            pod_info.add_detail(pod_detail)

            pods_with_errors.append(pod_info)

    # Print the pods with errors
    if pods_with_errors:
        print("Pods with errors:")
        for pod in pods_with_errors:
            pod.print_info()
            # List the files that start with the pod name in the selected folder
            pod_logs_files_path = os.path.join(kubernetes_path, selected_folder, 'logs')

    else:
        print("No pods with errors found.")

    
    


# Test the main function
if __name__ == "__main__":
    main()