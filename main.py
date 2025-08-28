# main.py
import os
import json

# Custom imports
from utils import conf, load_cache, logging
from printer import Printer
from error_info import analyze_pods_without_errors, analyze_pods_with_errors, analyze_describe_pods_output, classify_pods
from user_inputs import get_user_id_from_user, get_case_info_dir_from_user, get_namespace_path_from_user, get_error_patterns_from_user_input
from mongodb_handler import load_mongodb
from thefuzz import fuzz



            
def main():
    # Check if cache.json exists using the relataive path to where this script is located
    logging.info("START")
    cache = load_cache()
    
    mongo = load_mongodb()
    if mongo:
        error_patterns = mongo.get_default_error_patterns()
        user_id = get_user_id_from_user(mongo)
        
        error_patterns = get_error_patterns_from_user_input(user_id, mongo, error_patterns, cache)
    else:
        error_patterns = conf["log_error_patterns"]


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
        
        user_defined_dict = mongo.get_user_patterns(user_id)
        default_log_dict = mongo.get_default_error_patterns()
        
        update_default_flag = False
        new_patterns_added = []
        
        confirm_promotion = input("\nDo you want to update the default dictionary? (yes - default/no): ").strip()
            
        if confirm_promotion in conf["yes_list"]:
            for category, user_patterns_list in user_defined_dict.items():
                for user_pattern in user_patterns_list:
                    # Check if this pattern exists in ANY category of the default dict
                    exists_anywhere = any(
                        fuzz.ratio(user_pattern, default_pattern) >= 80
                        for patterns in default_log_dict.values()
                        for default_pattern in patterns
                    )

                    if exists_anywhere:
                        continue  # Pattern already exists somewhere, then it is skipped

                    # If pattern doesn't exist anywhere, either add to a preexisting category
                    if category in default_log_dict:
                        # Category exists → just append
                        default_log_dict[category].append(user_pattern)
                        new_patterns_added.append((category, user_pattern))
                    else:
                        # Category doesn't exist, then creates new category
                        default_log_dict[category] = [user_pattern]
                        new_patterns_added.append((category, user_pattern))

                    update_default_flag = True

            if update_default_flag:
                mongo.update_error_patterns(default_log_dict)
                print("\nDefault log dictionary has been updated!")
                for category, pattern in new_patterns_added:
                    print(f" -[{category}] {pattern}")
                logging.info("Default log dict updated with these new patterns")
            else:
                print("\nNo new patterns added")
                logging.info("No new patterns added to default dict as they already exist")
    else:
        print("Default log dictionary was not updated.")
        logging.info("User chose not to update the default log dictionary.")

                    

if __name__ == "__main__":
    main()
