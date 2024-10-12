from typing import Tuple
from humanlayer import HumanLayer
from openai import OpenAI
import subprocess

from logger import logger
import json

hl = HumanLayer()

from src.model.runbook import Runbook, Step

EXECUTE_STEP_PROMPT_FILE="include/prompts/execute_step.txt"

@hl.require_approval()
def execute(cmd: str) -> Tuple[str, bool]:
    """
    executes a bash comand and returns the output as 
    well as whether the command succeeded or not
    """
    try:
        # Execute the command
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Return stdout, stderr, and success status (True if successful)
        return f"stdout: {result.stdout}\nstderr: {result.stderr}", True
    except subprocess.CalledProcessError as e:
        # Return stdout, stderr, and failure status (False if failed)
        return f"stdout: {e.stdout}\nstderr: {e.stderr}", True

shell_tools_openai = [
    {
        "type": "function",
        "function": {
            "name": "execute",
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string"},
                },
                "required": ["cmd"],
            },
        },
    },
]

class RunBookExecutor:
    """
    Class to execute runbooks.
    """
    def __init__(self) -> None:
        self.client = OpenAI()

    def bailout(self, step: Step, execution_output: str, num_retries: int = 3) -> Tuple[bool, str]:
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
        prompt = ""
        messages = []

        with open(EXECUTE_STEP_PROMPT_FILE, "r", encoding="utf8") as fp:
            prompt = fp.read()
            messages += [{"role": "system", "content": prompt}]

            user_content = f"""
            Inputs:
            cmds: [{','.join(step.allowed_cmds)}]
            desc: {step.description}
            """

            messages += [{"role": "user", "content": user_content}]

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=shell_tools_openai,
            response_format={"type": "json_object"}
        )

        while response.choices[0].finish_reason != "stop":
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                messages.append(response_message)  # extend conversation with assistant's reply
                logger.info(
                    "last message led to %s tool calls: %s",
                    len(tool_calls),
                    [(tool_call.function.name, tool_call.function.arguments) for tool_call in tool_calls],
                )

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    logger.info("CALL tool %s with %s", function_name, function_args)

                    function_response_json: str

                    try:
                        function_response = execute(**function_args)
                        function_response_json = json.dumps(function_response)
                    except Exception as e:
                        function_response_json = json.dumps(
                            {
                                "error": str(e),
                            }
                        )

                    logger.info(
                        "tool %s responded with %s",
                        function_name,
                        function_response_json[:200],
                    )
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response_json,
                        }
                    )  # extend conversation with function response

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=shell_tools_openai,
            )

        return success, response.choices[0].message.content

    def run_book(self, rb: Runbook) -> Tuple[bool, str]:
        """
        Executes a runbook and returns the final response.

        returns a tuple of (whether the runbook executed successfully, str response to send to the user)
        """

        for step in rb.steps:
            # 1. execute step.
            success, response = self.execute_step(step)
            print(response)

            if not success:
                success, response = self.bailout(step, response)

        return "Done"
