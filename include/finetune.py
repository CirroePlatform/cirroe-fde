"""
This file contains the code to collect data on the fly for finetuning Cirroe.
"""

from include.constants import DEFAULT_BUG_OUTPUT_PATH
from src.model.issue import Issue
from typing import TextIO
import json

class DatasetCollector:
    def __init__(self, bug_output_path: str = DEFAULT_BUG_OUTPUT_PATH):
        self.bug_output_path = bug_output_path
    
    def __write_jsonl_newline(self, fp: TextIO, **kwargs):
        fp.write(json.dumps(kwargs) + "\n")
    
    def collect_is_bug_output(self, issue: Issue, actual_decision: bool):
        with open(self.bug_output_path, "a") as f:
            self.__write_jsonl_newline(f, issue=issue.description, actual_decision=actual_decision)
