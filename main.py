# main.py

import os

def main():
    # Get user input to specify the path to the get-k8s-info output
    k8s_file_path = input("Please enter the path to the get-k8s-info output file: ")

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
    print(f"You selected: {selected_folder}")


# Test the main function
if __name__ == "__main__":
    main()