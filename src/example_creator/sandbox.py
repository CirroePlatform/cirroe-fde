"""
This file is used to test the example creator tools by executing code examples in a sandbox.
"""

import subprocess
import sys
import os
from typing import Tuple
from enum import Enum


class Language(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"


class Sandbox:
    """
    A sandbox environment for safely executing and testing code examples
    """

    def __init__(self):
        # Verify node/npm is installed for TypeScript execution
        self._verify_typescript_deps()

    def _verify_typescript_deps(self):
        """Verifies TypeScript dependencies are installed"""
        try:
            subprocess.run(["node", "--version"], capture_output=True, check=True)
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(
                "Warning: Node.js/npm not found. TypeScript execution will not be available."
            )

    def run_code(self, code: str, language: Language) -> Tuple[str, str]:
        """
        Executes the provided code in a sandbox environment and returns the output

        Args:
            code (str): The code to execute
            language (Language): The programming language of the code

        Returns:
            Tuple[str, str]: A tuple containing (stdout, stderr) from code execution
        """
        if language == Language.PYTHON:
            return self._run_python(code)
        elif language == Language.TYPESCRIPT:
            return self._run_typescript(code)
        else:
            return "", f"Unsupported language: {language}"

    def _run_python(self, code: str) -> Tuple[str, str]:
        """Executes Python code"""
        temp_file = "temp.py"
        try:
            with open(temp_file, "w") as f:
                f.write(code)

            process = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate()
            return stdout.strip(), stderr.strip()

        except Exception as e:
            return "", str(e)

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def _run_typescript(self, code: str) -> Tuple[str, str]:
        """Executes TypeScript code"""
        temp_file = "temp.ts"
        try:
            # Create temporary TypeScript file
            with open(temp_file, "w") as f:
                f.write(code)

            # Compile TypeScript to JavaScript
            compile_process = subprocess.run(
                ["npx", "tsc", temp_file], capture_output=True, text=True
            )

            if compile_process.returncode != 0:
                return "", f"TypeScript compilation error:\n{compile_process.stderr}"

            # Execute the compiled JavaScript
            process = subprocess.Popen(
                ["node", temp_file.replace(".ts", ".js")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate()
            return stdout.strip(), stderr.strip()

        except Exception as e:
            return "", str(e)

        finally:
            # Cleanup temporary files
            for ext in [".ts", ".js"]:
                temp = temp_file.replace(".ts", ext)
                if os.path.exists(temp):
                    os.remove(temp)

    def format_output(self, stdout: str, stderr: str) -> str:
        """
        Formats the stdout and stderr into a readable string

        Args:
            stdout (str): Standard output from code execution
            stderr (str): Standard error from code execution

        Returns:
            str: Formatted output string
        """
        output = []

        if stdout:
            output.append("Standard Output:")
            output.append(stdout)

        if stderr:
            if output:
                output.append("\n")
            output.append("Standard Error:")
            output.append(stderr)

        return "\n".join(output)
