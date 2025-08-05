### Automate k8s troubleshooting 
The purpose of this project is to automate situation appraisal procedure of the get-k8s-info.sh output provided by SAS.

### TODO
1. Read kubectl get pods output and analyze pods in abnormal state
   - Error
   - 0/1     Running
   - CrashLoopBackOff
   - 0/2     Init:2/4
2. Read the logs of the pods that are in an abnormal state
3. Analyze the logs and organize errors or warnings that might be the cause of the issue
4. Read the output of the kubectl describe command of the pods that are in an abnormal state
5. Analyze the output and organize errors or warnings that might be the cause of the issue
6. Search for other related issues that causes the pod to be inoperable

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
