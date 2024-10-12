from typing import Tuple

from src.model.runbook import Runbook, Step

EXECUTE_STEP_PROMPT_FILE="include/prompts/execute_step.txt"

class RunBookExecutor:
    """
    Class to execute runbooks.
    """

    def debug_failed_step(self, step: Step, execution_output: str, num_retries: int = 3) -> Tuple[bool, str]:
        """
        Debug the failed step given the schema and execution_output.
        
        returns a success and expected output. Will execute num_retries times
        """
        return False, execution_output

    def execute_step(self, step: Step) -> Tuple[bool, str]:
        """
        Executes a step and returns any potential output as well 
        the success of the execution
        """
        success = False
        response = ""

        with open(EXECUTE_STEP_PROMPT_FILE, "r", encoding="utf8") as fp:
            prompt = fp.read()

        return success, response

    def run_book(self, rb: Runbook) -> Tuple[bool, str]:
        """
        Executes a runbook and returns the final response.
        
        returns a tuple of (whether the runbook executed successfully, str response to send to the user)
        """

        for step in rb.steps:
            # 1. execute step.
            success, response = self.execute_step(step)
            
            if not success:
                success, response = self.debug_failed_step(step, response)

        return "Done"
