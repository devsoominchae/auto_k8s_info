from dotenv import load_dotenv
import os
from mongodb_handler import MongoHandler

# Load .env file from current directory
load_dotenv()

# Read credentials and config from environment variables
username = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASS")
cluster = os.getenv("MONGO_CLUSTER", "logdictionary.ziwndyc.mongodb.net")
db_name = os.getenv("MONGO_DB_NAME", "log_config")

# Ensure required credentials exist
if not username or not password:
    raise ValueError("MongoDB username or password not set in .env file.")

# Construct URI
uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority&appName=logDictionary"

# Define patterns to update
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

# Connect and update MongoDB
mongo = MongoHandler(uri, db_name)
mongo.update_error_patterns(conf_patterns)

print("Updated!")
