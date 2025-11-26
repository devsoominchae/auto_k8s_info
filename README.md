# 🚀 Automate Kubernetes Troubleshooting

Instead of manually digging through pod statuses and logs, this tool helps you quickly identify abnormal pods, analyze their logs, and highlight potential root causes.

---

## ✅ What It Does
- Reads `get-k8s-info` output and flags abnormal pods such as:
  - `Error`
  - `0/1 Running`
  - `CrashLoopBackOff`
  - `Init:2/4` (stuck during initialization)
- Reads logs for abnormal pods
- Organizes errors and warnings that could explain the issue
- Searches for related issues causing pod failures
- Finds other pods that show similar errors
- Stores error patterns in a database and reuses them for faster troubleshooting

---

## 📝 Roadmap

### Implemented
✔ Pod state analysis  
✔ Log analysis for failed pods  
✔ Error/warning extraction  
✔ Related-issue detection  
✔ Cross-pod error checking  
✔ Database storage of error patterns  

---

## ⚙️ How to use the default dictionary

:one: Use get-k8s-info tool to gain folder containing information of their viya 4 environment  
:two: Make sure it is decompressed!  
:three: Go to the releases page on the right, and download conf.json, error.patterns.json and main.exe  
:four: Run main.exe
######
    > .\main.exe
:five: Leave the input blank to use the default dictionary!
######
    Select a user by number or by user ID or enter a new user ID.
    1. jobyun
    2. sochae
    3. default
    Enter choice:
    Username must be longer than 5 characters. Current input: 
    Username :  
    Length : 0 
    Using default error patterns.
    Error patterns :
     {
     ...
:six: Paste the path to the folder we want to investigate!
######
    Please enter the path to the get-k8s-info output file: C:\auto_k8s_info\get_k8s_info\CS0305203_20250910_163413
:seven: Select the namespace we want to investigate!
######
    Available folders under kubernetes:
    1. cert-manager
    2. clusterwide
    3. ingress-nginx
    4. kube-system
    5. logging
    6. monitoring
    7. nfs-client
    8. sasviya4
    Enter choice: 8
    Your choice: sasviya4
:eight: Wait for your results - CLI shows a simplified overview, while a detailed version is stored in the namespace we investigated with the name "all_errors.json" or in the "output" folder with the format auto_k8s_CASENUMBER_NAMESPACE_YYYYMMDD_HHMMSS.txt

## 👷 How to use your own personal dictionary

:one: Follow the same steps up to step 4  
:two: Input a new id - this will create a personal file locally (for now)  
:three: Navigate the menu to export the file...  
:four: Edit the file to your liking - we kept a default dictionary for easy understanding of format 😄  
:five: Upload your file by inputting the path  
:six: Now you are ready to use your own personal dictionary for analysis!  
:seven: After analysis, it can be stored to your personal dictionary, or even upload to the main public dictionary!  

---

## :chart_with_upwards_trend: User report in Visual Analytics
- [auto_k8s_info Dashboard](https://trck1076843.trc.sas.com/SASVisualAnalytics/?reportUri=%2Freports%2Freports%2F6770e85c-7f57-413b-9783-cd43a2ce759c&reportViewOnly=true&reportContextBar=false&pageNavigation=false&sas-welcome=false)
- User ID: sasuser
- Password: sasuser
---

## 😠 Still Stuck? Dont Worry...

Check the demo below!  
- [Basic demo for auto k8s tool](https://youtu.be/hWbZIx9A_Lg)
