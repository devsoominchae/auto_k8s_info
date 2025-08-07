from mongodb_handler import MongoHandler
#Simple test to update error patterns in MongoDB - will be added to main.py later
conf_patterns = {
    "CAS Control Issues": ["no ready CAS servers", "cas-control is not ready"],
    "Telemetry Warnings": ["OpenTelemetry support not installed"],
    "Readiness Check Failures": [
            "check \"sas-endpoints-ready\" failed",
            "no available addresses",
            "endpoints have no available addresses",
            "0 available addresses",
            "failed readiness check"
        ]
}

mongo = MongoHandler("mongodb+srv://sasadm:Orion123@logdictionary.ziwndyc.mongodb.net/?retryWrites=true&w=majority&appName=logDictionary")
mongo.update_error_patterns(conf_patterns)

print("Updated!")