### Automate k8s troubleshooting 
The purpose of this project is to automate situation appraisal procedure of the get-k8s-info.sh output provided by SAS.

### TODO
1. Find status of other components that are related to the abnormal pod (PVC, Secret, Deployment etc.)
2. Add feature to let users modify error patterns
3. Let users create their own patterns


### DONE
1. Read kubectl get pods output and analyze pods in abnormal state
   - Error
   - 0/1     Running
   - CrashLoopBackOff
   - 0/2     Init:2/4
2. Read the logs of the pods that are in an abnormal state
3. Analyze the logs and organize errors or warnings that might be the cause of the issue
4. Search for other related issues that causes the pod to be inoperable
5. Find any other pod logs that contain errors
6. Store error patterns on a database and find it in the logs

### Notes
Dont forget to install packages using the code below (or just pip install pymongo)

```
pip install -r requirements.txt
```

### Testing
First you will need an unzipped sample get-k8s-info.sh output. 
######
    python main.py

Sample output
######
    Please enter the path to the get-k8s-info output file: <PROJECT_PATH>\auto_k8s_info\sample_data\CS0287492_20250731_102025
    Available folders under kubernetes:
    1: cert-manager
    2: cert-utils-operator
    3: clusterwide
    4: kube-system
    5: openshift-ingress
    6: viya-dev-ns
    7: viya-test-ns
    Please select a folder by number: 6
    You selected: viya-dev-ns

You can check the sample txt output auto_k8s_mis-viya_20250805_161819.txt

### conf.json file usage
######
    {
    "cache" : "cache.json", // Name of the cache file that contains the information you entered previously.
    "cache_default" : { // Default structure of cache.json file. This will automatically be created if it doesn't exist.
        "saved_case_info_dir": ""
    },
    "output_folder" : "output", // Destination directory of there the result will be saved. This can be changed
    "logging" : { // Logging information. Do not change this value.
        "level": "INFO",
        "format": "%(asctime)s %(levelname)s %(message)s"
    },
    "yes_list" : ["yes", "y", "Y", "Yes", "", "YES"], // All option that will be considered yes. All other options will be no. Do not change this.
    "invalid_windows_path_chars": ["<", ">", "\"", "/", "|", "?", "*"], // Full paths containing invalid characters will be removed.
    "describe_pods_error_patterns" : { // This defines the patterns that will be defined as abnormal in the kubectl describe pods output. This program will go line by line and will look for the lines that contain the string(ex. "Sample pattern to find") in the list. This can be changed/added by the user.
        "Warning" : ["Warning"],
        "Sample" : ["Sample pattern to find"]
    },
    "get_pods_error_patterns" : { // This defines the patterns that will be defined as abnormal in the kubectl get pods output. We define as abnormal if all the elements in the list(ex. both "0/1" and "Running") is in a line of the file. This can be changed/added by the user.
        "Error": ["Error"],
        "Running No Pods": ["0/", "Running"],
        "Hanged in Init": ["Init:"],
        "Crashed": ["CrashLoopBackOff"]
    },
    "log_error_patterns" : { // This defines the patterns that will be defined as abnormal in the kubectl get pods output. We define as abnormal if one the elements in the list(ex. "no ready CAS servers" or "cas-control is not ready") is in a line of the file. This can be changed/added by the user.
        "CAS Control Issues": [
            "no ready CAS servers",
            "cas-control is not ready"
        ]
    }
}
