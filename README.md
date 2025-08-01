### The purpose of this project is to automate situation appraisal procedures of the get-k8s-info.sh output provided by SAS.

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
