"""
This file is used to test the example creator tools by executing code examples in a sandbox.
"""

import subprocess
import sys
import os
from typing import Tuple, Dict, Any
from enum import Enum
import e2b
from github import Github
import re
import logging
from datetime import datetime


class Language(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"


class Sandbox:
    """
    A sandbox environment for safely executing and testing code examples
    """

    def __init__(self):
        self.gh = Github(os.getenv("GITHUB_TOKEN"))
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

    async def run_code_e2b(self, code_files: Dict[str, str], execution_command: str) -> Tuple[str, str]:
        """
        Executes code in E2B sandbox environment

        Args:
            code_files: Dictionary mapping filenames to code content
            execution_command: Command to execute the code (e.g. "python main.py" or "npm start")

        Returns:
            Tuple of (stdout, stderr)
        """
        try:
            # Create E2B session
            session = await e2b.Session.create(id="Sandbox", cwd="/code")

            # Create project directory structure and write files
            for filepath, content in code_files.items():
                # Create any necessary subdirectories
                dir_path = os.path.dirname(filepath)
                if dir_path:
                    await session.run(f"mkdir -p {dir_path}")
                
                # Write the file
                await session.write_file(filepath, content)

            # Install dependencies if package.json exists
            if "package.json" in code_files:
                await session.run("npm install")

            # Install TypeScript globally if any .ts files
            if any(f.endswith('.ts') for f in code_files.keys()):
                await session.run("npm install -g typescript")
                # Compile TypeScript files
                ts_files = [f for f in code_files.keys() if f.endswith('.ts')]
                if ts_files:
                    await session.run("tsc " + " ".join(ts_files))

            # Execute the provided command
            result = await session.run(execution_command)

            await session.close()
            return result.stdout, result.stderr

        except Exception as e:
            logging.error(f"E2B execution error: {e}")
            return "", str(e)

    def create_github_pr(self, code_string: str, repo_name: str) -> str:
        """
        Creates a PR on GitHub with example code

        Args:
            code_string: Example code in format from execute_creation.txt
            repo_name: Target repository name (format: owner/repo)

        Returns:
            PR URL if successful, error message if not
        """
        try:
            # Parse files from code string
            files = self.parse_example_files(code_string)
            if not files:
                return "Error: No valid files found in code string"

            # Get repo
            repo = self.gh.get_repo(repo_name)

            # Create new branch
            base_branch = repo.default_branch
            new_branch = f"example-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            base_ref = repo.get_git_ref(f"heads/{base_branch}")
            repo.create_git_ref(f"refs/heads/{new_branch}", base_ref.object.sha)

            # Create/update files in new branch
            commit_message = "Add new example"
            for file_path, content in files.items():
                try:
                    # Check if file exists
                    existing_file = repo.get_contents(
                        f"examples/{file_path}", ref=new_branch
                    )
                    repo.update_file(
                        f"examples/{file_path}",
                        commit_message,
                        content,
                        existing_file.sha,
                        branch=new_branch,
                    )
                except:
                    # File doesn't exist, create it
                    repo.create_file(
                        f"examples/{file_path}",
                        commit_message,
                        content,
                        branch=new_branch,
                    )

            # Create PR
            pr = repo.create_pull(
                title="Add new example",
                body="Automatically generated example code",
                head=new_branch,
                base=base_branch,
            )

            return pr.html_url

        except Exception as e:
            logging.error(f"GitHub PR creation error: {e}")
            return f"Error creating PR: {str(e)}"

    def parse_example_files(self, code_string: str) -> Dict[str, str]:
        """
        Parses example files from code string format

        Args:
            code_string: String containing file definitions

        Returns:
            Dictionary mapping file paths to contents
        """
        files = {}
        # Extract content between <fpath_*> tags
        pattern = r"<fpath_([^>]+)>(.*?)</fpath_\1>"
        matches = re.finditer(pattern, code_string, re.DOTALL)

        for match in matches:
            file_path = match.group(1)
            content = match.group(2)
            files[file_path] = content.strip()

        return files
