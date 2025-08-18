# main.py
import os
import sys
import json

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter


# Custom imports
from utils import conf, load_cache, get_case_info_dir_from_user, get_namespace_path_from_user, get_env_file, logging
from printer import Printer
from pod_info import PodInfo
from error_info import ErrorInfoHolder

from mongodb_handler import MongoHandler
from dotenv import load_dotenv
from pprint import pprint


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
def log_file_collection(namespace_path, pods_with_errors, printer):
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
                for line in log_file:
                    for category, patterns in conf.get('log_error_patterns', {}).items():
                        if any(p in line for p in patterns):
                            pod.add_error_once_by_message(file_name, category, line)
                            break
                    
                # pod.add_error_once_by_message(file_name, "Most Recent Record", log_file[-1].strip())

def analyze_pods_without_errors(namespace_path, pods_without_errors, printer):
    error_info_holder = ErrorInfoHolder(printer)
    printer_console = Printer(os.path.basename(namespace_path), mode="console")
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
            with open(file_name, "r", encoding="utf-8", errors="ignore") as log_file:
                for line in log_file:
                    for category, patterns in conf.get('log_error_patterns', {}).items():
                        if any(p in line for p in patterns):
                            error_info = error_info_holder.format_error(line, file_name, category)
                            error_info_holder.add_error(error_info)

    return error_info_holder

def custom_error_patterns(mongo_handler):
    add_custom = input("\nDo you want to add custom error patterns? (y/n): ").strip().lower()
    if add_custom not in ['y', 'yes']:
        return {}
    temp_patterns = {}
    while True:
        custom_msg = input("Enter the custom error message (or press enter to stop): ").strip()
        if not custom_msg:
            break
    
        #Pre defined categories within mongodb
        existing_patterns = mongo_handler.get_error_patterns()
        existing_categories = list(existing_patterns.keys())
        #To print nicely the categories
        print("\nExisting categories in MongoDB:")
        for idx, cat in enumerate(existing_categories, 1):
            print(f"  {idx}. {cat}")
        
        # Create a completer
        category_completer = WordCompleter(existing_categories, ignore_case=True)

        # Prompt with autocomplete
        selected_category = prompt("Enter a category to add this message to (or type new one): ", completer=category_completer).strip()

        
        if selected_category not in existing_categories:
            create_new = input(f"'{selected_category}' not found. Create new category? (y/n): ").strip().lower()
            if create_new not in ['y', 'yes']:
                continue    
        current_patterns = existing_patterns.get(selected_category, [])
        if custom_msg in current_patterns:
            print("Message already exists in this category. Skipping.")
            continue        
        if selected_category not in temp_patterns:
            temp_patterns[selected_category] = []
        temp_patterns[selected_category].append(custom_msg)
        print(f"Added to temp: [{selected_category}] -> {custom_msg}")
    if temp_patterns:
        pprint(temp_patterns)
        print("\nThese patterns are temporary, used for this session only.")
                   
    return temp_patterns

            
def main():
    # Check if cache.json exists using the relataive path to where this script is located
    logging.info("START")
    try:
        get_env_file() 
        load_dotenv()
        mongo_uri = os.getenv("MONGODB_URI")

        if not mongo_uri:
            print("MongoDB URI not found in environment variables.")
            logging.error("MongoDB URI not found in environment variables.")
        else:

            mongo = MongoHandler(uri=mongo_uri)

            # Replace conf log_error_patterns with patterns from MongoDB

            #calls the log pattern dict from mongodb, and merges it with the custom user patterns (if any)
            mongo_patterns = mongo.get_error_patterns()
            temp_user_patterns = custom_error_patterns(mongo)
            for cat, patterns in temp_user_patterns.items():
                if cat in mongo_patterns:
                    mongo_patterns[cat].extend(p for p in patterns if p not in mongo_patterns[cat])
                else:
                    mongo_patterns[cat] = patterns
            conf["log_error_patterns"] = mongo_patterns
            

    except Exception as e:
        print(f"Error loading MongoDB configuration: {e}.\nUsing default patterns from conf.json.")
        logging.error(f"Error loading MongoDB configuration: {e}. Using default patterns from conf.json.")

    print("Error patterns :\n", json.dumps(conf["log_error_patterns"], indent=4))

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

    log_file_collection(namespace_path, pods_with_errors, printer)

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
    
    error_info_holder = analyze_pods_without_errors(namespace_path, pods_without_errors, printer)
    error_info_holder.print_pods_by_error_category()
    error_info_holder.print_containers_by_error_category()
    
    if temp_user_patterns:
        confirm_custom_patterns = input("\nDo you want to permanently save the custom error patterns you used? (y/n): ").strip().lower()
        if confirm_custom_patterns in ['y', 'yes']:
            for cat, msgs in temp_user_patterns.items():
                for msg in msgs:
                    mongo.add_error_pattern(cat, msg)
            print("Custom patterns saved to MongoDB.")
    

if __name__ == "__main__":
    main()
