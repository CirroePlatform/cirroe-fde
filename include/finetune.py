"""
This file contains the code to collect data on the fly for finetuning Cirroe.
"""

from include.constants import DEFAULT_NEEDS_DEV_TEAM_OUTPUT_PATH
from src.model.issue import Issue
from typing import TextIO
import json


class DatasetCollector:
    def __init__(
        self, needs_dev_team_output_path: str = DEFAULT_NEEDS_DEV_TEAM_OUTPUT_PATH
    ):
        self.needs_dev_team_output_path = needs_dev_team_output_path

    def __write_jsonl_newline(self, fp: TextIO, **kwargs):
        fp.write(json.dumps(kwargs) + "\n")

    def collect_needs_dev_team_output(
        self, issue: Issue, actual_decision: bool, additional_info: str
    ):
        with open(self.needs_dev_team_output_path, "a") as f:
            self.__write_jsonl_newline(
                f,
                issue=issue.description,
                actual_decision=actual_decision,
                additional_info=additional_info,
            )
