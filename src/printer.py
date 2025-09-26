# printer.py

import os
import json
from datetime import datetime

# Custom imports
from utils import conf, logging

PRINTER_MODE = ["console", "file", "both"]
DATETIME_FORMAT = "%Y%m%d_%H%M%S"


class Printer:
    def __init__(self, namespace_path, mode="both"):
        namespace_path = namespace_path
        namespace = os.path.basename(namespace_path)
        try:
            case_number = [i for i in namespace_path.split(os.sep) if i.startswith("CS")][0].split("_")[0]
        except Exception as e:
            logging.info(f"Error parsing case number from file path: {e}")
            case_number = ""
        
        logging.info(f"\nInitializing Printer with \nNamespace: {namespace} \nNode: {mode} \nCase number: {case_number}")
        assert mode in PRINTER_MODE, f"Invalid printer mode: {mode}. Choose from {PRINTER_MODE}."
        self.mode = mode
        os.makedirs(os.path.join("output", case_number), exist_ok=True)
        self.file_path = os.path.join(case_number, f"auto_k8s_{namespace}_{datetime.now().strftime(DATETIME_FORMAT)}.txt") if mode in ["file", "both"] else None
        
        if not os.path.exists(conf['output_folder']):
            os.makedirs(conf['output_folder'])
        self.file_path = os.path.join(conf['output_folder'], self.file_path) if mode in ["file", "both"] else None

        logging.info(f"Printer file path set to: {self.file_path}")
    
    def write_to_file(self, message):
        if self.file_path:
            with open(self.file_path, 'a', encoding='utf-8') as file:
                file.write(message + '\n')
    
    def print_message(self, message, print_level=1, end_=None, flush_=False):
        if conf['print_level'] >= print_level:
            match self.mode:
                case "console":
                    print(message, end=end_, flush=flush_)
                case "file":
                    self.write_to_file(message)
                case "both":
                    print(message)
                    self.write_to_file(message)
