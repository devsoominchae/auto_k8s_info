import re

from utils import conf

IP_ADDRESS_PATTERN = r'\b(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\b'
PORT_PATTERN = r':([1-9]\d{0,4})\b'


def clean_ip_address(line):    
    text_with_ip_replaced = re.sub(IP_ADDRESS_PATTERN, 'IP_ADDRESS', line)
    return text_with_ip_replaced


def clean_port(line):
    text_with_port_replaced = re.sub(PORT_PATTERN, ':PORT', line)
    return text_with_port_replaced

CLEANER_FUNC_DICT = {
    "ip_address" : clean_ip_address,
    "port" : clean_port
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
