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

## ⚙️ Step by Step Guide

:one: Use get-k8s-info tool to gain folder containing information of their viya 4 environment  
:two: Make sure it is decompressed!  
:three: Go to the releases page on the right, and download conf.json, error.patterns.json and main.exe  
:four: Run main.exe...  
:five: Either leave blank when asked for an input - or use an ID if you have stored a personal log dictionary.  
:six: Paste the path to the folder we want to investigate!  
:seven: Select the namespace we want to investigate!  
8️⃣: Wait for your results - CLI shows a simplified overview, while a detailed version is stored in the namespace we investigated with the name "all_errors.json"  

