# printer.py

import os
import json
from datetime import datetime

# Custom imports
from logging_conf import logging

PRINTER_MODE = ["console", "file", "both"]
DATETIME_FORMAT = "%Y%m%d_%H%M%S"

with open('conf.json', 'r', encoding='utf-8') as f:
    conf = json.load(f)

class Printer:
    def __init__(self, namespace, mode="both"):
        logging.info(f"Initializing Printer with namespace: {namespace} and mode: {mode}")
        assert mode in PRINTER_MODE, f"Invalid printer mode: {mode}. Choose from {PRINTER_MODE}."
        self.mode = mode
        self.file_path = f"auto_k8s_{namespace}_{datetime.now().strftime(DATETIME_FORMAT)}.txt" if mode in ["file", "both"] else None
        
        if not os.path.exists(conf['output_folder']):
            os.makedirs(conf['output_folder'])
        self.file_path = os.path.join(conf['output_folder'], self.file_path) if mode in ["file", "both"] else None

        logging.info(f"Printer file path set to: {self.file_path}")
    
    def write_to_file(self, message):
        if self.file_path:
            with open(self.file_path, 'a', encoding='utf-8') as file:
                file.write(message + '\n')
    
    def print_message(self, message, print_level=1):
        if conf['print_level'] >= print_level:
            match self.mode:
                case "console":
                    print(message)
                    self.write_to_file(message)
                case "file":
                    self.write_to_file(message)
                case "both":
                    print(message)
                    self.write_to_file(message)


        