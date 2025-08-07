from mongodb_handler import MongoHandler
import getpass

# Prompt user
username = input("Enter MongoDB username: ")
password = getpass.getpass("Enter MongoDB password: ")

# Construct URI dynamically using user input
uri = f"mongodb+srv://{username}:{password}@logdictionary.ziwndyc.mongodb.net/?retryWrites=true&w=majority&appName=logDictionary"

# Define patterns
conf_patterns = {
    "CAS Control Issues": ["no ready CAS servers", "cas-control is not ready"],
    "Telemetry Warnings": ["OpenTelemetry support not installed"],
    "Readiness Check Failures": [
        'check "sas-endpoints-ready" failed',
        "no available addresses",
        "endpoints have no available addresses",
        "0 available addresses",
        "failed readiness check"
    ]
}

# Use dynamic URI to connect
mongo = MongoHandler(uri)
mongo.update_error_patterns(conf_patterns)

print("Updated!")
