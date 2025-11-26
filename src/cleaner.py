import re

from utils import conf

IP_ADDRESS_PATTERN = r'\b(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\b'
PORT_PATTERN = r':([1-9]\d{0,4})\b'
JOB_NUMBER_PATTERN = r'(The job\s*")\d+(" has been terminated through the REST API\.)'
JOB_ID_PATTERN = r"(?<=job ID ')\d+(?=')"
POD_ID_PATTERN = r'-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-'
JOB_ID_PATTERN_AFTER_POD_ID = r'-POD_ID-\b(?:0|[1-9]\d{0,3})\b\"'


def clean_ip_address(line):    
    text_with_ip_replaced = re.sub(IP_ADDRESS_PATTERN, 'IP_ADDRESS', line)
    return text_with_ip_replaced


def clean_port(line):
    text_with_port_replaced = re.sub(PORT_PATTERN, ':PORT', line)
    return text_with_port_replaced

def clean_job_number(line):
    text_with_job_number_replaced = re.sub(JOB_NUMBER_PATTERN, 'The job "JOB_NUMBER" has been terminated through the REST API', line)
    return text_with_job_number_replaced    

def clean_job_id(line):
    text_with_job_id_replaced = re.sub(JOB_ID_PATTERN, 'job ID \'JOB_ID\'', line)
    return text_with_job_id_replaced 

def clean_pod_id(line):
    text_with_pod_id_replaced = re.sub(POD_ID_PATTERN, "-POD_ID-", line)
    return text_with_pod_id_replaced 

def clean_job_id_after_pod_id(line):
    text_with_job_id_after_pod_id_replaced = re.sub(JOB_ID_PATTERN_AFTER_POD_ID, "-POD_ID-JOB_ID", line)
    return text_with_job_id_after_pod_id_replaced 


CLEANER_FUNC_DICT = {
    "ip_address" : clean_ip_address,
    "port" : clean_port,
    "job_number": clean_job_number,
    "job_id" : clean_job_id,
    "pod_id" : clean_pod_id,
    "job_id_after_pod_id" : clean_job_id_after_pod_id
}

def get_full_cleaners():
    cleaners_conf = [key for key, value in conf.get("cleaner", {}).items() if value is True]
    cleaners = [CLEANER_FUNC_DICT[i] for i in cleaners_conf]
    return cleaners

def clean_log(line):
    cleaners = get_full_cleaners()
    for cleaner in cleaners:
        line = cleaner(line)
    
    return line

def normalize_logs(message: str) -> str:
    message = re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "DATETIME", message)
    message = re.sub(r"\s+", " ", message)
    return message.strip()
