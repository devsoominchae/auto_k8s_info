# main.py
import os
import json

from pprint import pprint
from dotenv import load_dotenv


# Custom imports
from utils import conf, load_cache, logging, load_json_from_path, get_env_file
from printer import Printer
from pod_info import PodInfo
from error_info import analyze_pods_without_errors, analyze_pods_with_errors, line_matches_error_patterns
from user_inputs import get_user_id_from_user, user_dict_has_valid_format, user_will_update_dict, user_will_create_new_id, get_case_info_dir_from_user, get_namespace_path_from_user, select_option
from mongodb_handler import MongoHandler


DOWNLOAD_UPLOAD_OPTIPONS = [
    "Download",
    "Upload",
    "Exit"
    ]

            
def main():
    # Check if cache.json exists using the relataive path to where this script is located
    logging.info("START")
    error_patterns = {}
    try:
        get_env_file() 
        load_dotenv()
        mongo_uri = os.getenv("MONGODB_URI")

        if not mongo_uri:
            print("MongoDB URI not found in environment variables.")
            logging.error("MongoDB URI not found in environment variables.")
        else:

            mongo = MongoHandler(uri=mongo_uri)

            error_patterns = mongo.get_default_error_patterns()
            user_id = get_user_id_from_user(mongo)
            if user_id != "default":
                if mongo.user_exists(user_id):
                    error_patterns = mongo.get_user_patterns(user_id)
                else:
                    user_will_create_new_id()
                print("Error patterns :\n", json.dumps(error_patterns, indent=4))
                if user_will_update_dict():
                    while True:
                        match select_option(DOWNLOAD_UPLOAD_OPTIPONS, tab_complete=True):
                            case "Download":
                                with open("error_patterns.json", "w", encoding="utf-8") as f:
                                    json.dump(error_patterns, f, ensure_ascii=False, indent=4)
                                    print(f"Error patterns file saved to {os.path.join(os.getcwd(), 'error_patterns.json')}")
                                    logging.info(f"Error patterns file saved to {os.path.join(os.getcwd(), 'error_patterns.json')}")
                            case "Upload":
                                user_dict_path = input("Enter the path to your JSON file: ").strip()
                                if user_dict_has_valid_format(user_dict_path):
                                    error_patterns = load_json_from_path(user_dict_path)
                                    print("Error patterns :\n", json.dumps(error_patterns, indent=4))
                                else:
                                    print(f"Using saved error patterns for user ID {user_id}")
                                    logging.info(f"Using saved error patterns for user ID {user_id}")
                            case "Exit":
                                break
                            
            else:
                print("Error patterns :\n", json.dumps(error_patterns, indent=4))

            

    except Exception as e:
        print(f"Error loading MongoDB configuration: {e}.\nUsing default patterns from conf.json.")
        logging.error(f"Error loading MongoDB configuration: {e}. Using default patterns from conf.json.")

    cache = load_cache()

    case_info_dir = get_case_info_dir_from_user(cache)

    namespace_path = get_namespace_path_from_user(case_info_dir)
    printer = Printer(os.path.basename(namespace_path), mode="both")

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

    for line in get_pods_output_lines[column_index + 1:]:
        matched, category = line_matches_error_patterns(line, conf.get("get_pods_error_patterns", {}), "all")
        pod_name = line.split()[0]
        pod_node = line.split()[reverse_node_name_index] if reverse_node_name_index != -1 else "unknown"
        if matched:
            pod_info = PodInfo(pod_name, category, pod_node, namespace_path, printer)
            pod_info.add_error(get_pods_output, line.strip())
            pods_with_errors.append(pod_info)
        elif not matched and pod_name != "NAME":
            pod_info = PodInfo(pod_name, "No Issues", pod_node, namespace_path, printer)
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

    analyze_pods_with_errors(namespace_path, pods_with_errors, printer, error_patterns)

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
    
    error_info_holder = analyze_pods_without_errors(namespace_path, pods_without_errors, printer, error_patterns)
    error_info_holder.print_pods_by_error_category()
    error_info_holder.print_containers_by_error_category()
    
    confirm_custom_patterns = input("\nDo you want to permanently save the custom error patterns you used? (yes - default/no): ").strip()
    if confirm_custom_patterns in conf["yes_list"]:
        mongo.update_user_patterns(user_id, error_patterns)
        print(f"Error patterns has been updated for user {user_id}")
        logging.info(f"Error patterns has been updated for user {user_id}")
    else:
        print(f"Error patterns for user {user_id} has not been updated.")
        logging.info(f"Error patterns for user {user_id} has not been updated.")
    print(f"Current error pattern for {user_id}:")
    print("Error patterns :\n", json.dumps(mongo.get_user_patterns(user_id), indent=4))

    

if __name__ == "__main__":
    main()
