# main.py
import os
import json

# Custom imports
from utils import conf, load_cache, logging
from printer import Printer
from error_info import analyze_pods_without_errors, analyze_pods_with_errors, analyze_describe_pods_output, classify_pods
from user_inputs import get_user_id_from_user, get_case_info_dir_from_user, get_namespace_path_from_user, get_error_patterns_from_user_input
from mongodb_handler import load_mongodb



            
def main():
    # Check if cache.json exists using the relataive path to where this script is located
    logging.info("START")
    
    mongo = load_mongodb()
    error_patterns = mongo.get_default_error_patterns()
    user_id = get_user_id_from_user(mongo)
    
    error_patterns = get_error_patterns_from_user_input(user_id, mongo, error_patterns)

    cache = load_cache()

    case_info_dir = get_case_info_dir_from_user(cache)

    namespace_path = get_namespace_path_from_user(case_info_dir)
    printer = Printer(os.path.basename(namespace_path), mode="both")
    
    pods_with_errors, pods_without_errors = classify_pods(namespace_path, printer)

    pods_with_errors = analyze_describe_pods_output(namespace_path, pods_with_errors)

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
