from typing import List

from src.model.runbook import Runbook, Step
from src.model.issue import Issue


class RunBookExecutor:
    """
    Class to execute runbooks.
    """

    def get_runbook_for_issue(self, issue: Issue, runbooks: List[Runbook]):
        """
        Returns some runbook that matches the provided issue. TODO Need to do classification here.
        """
        return Runbook(rid=0, steps=[Step(sid=1, description="", allowed_cmds=[""])])

    # class Step(BaseModel):
    #     sid: UUID
    #     description: str
    #     allowed_cmds: List[str]
    #     next_steps: List[UUID]
    def execute_step(self, step: Step) -> str:
        """
        Executes a step and returns any potential output.
        """
        pass

    def run_book(self, rb: Runbook) -> str:
        """
        Executes a runbook and returns the final response.
        """

        for step in rb.steps:
            # 1. execute step.
            pass

        return "Done"
