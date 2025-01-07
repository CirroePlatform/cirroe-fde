"""
This file is used to test the example creator tools by executing code examples in a sandbox.
"""

import traceback
import subprocess
import sys
import json
import os
from typing import Tuple, Dict
from enum import Enum
from e2b import Sandbox as e2b_sandbox
from e2b import CommandResult
import re
import asyncio
import logging
from include.constants import GITHUB_API_BASE
import requests


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

        self.e2b_api_key = os.getenv("E2B_API_KEY")

        self.gh_token = os.getenv("GITHUB_TEST_TOKEN")
        self.github_headers = {
            "Authorization": f"Bearer {self.gh_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

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

    def run_code_e2b(
        self, code_files: str | Dict[str, str], execution_command: str
    ) -> CommandResult:
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
            sandbox = e2b_sandbox(
                timeout=60,
                api_key=self.e2b_api_key,
            )

            # Create project directory structure and write files
            if isinstance(code_files, str):
                code_files = json.loads(code_files)

            for filepath, content in code_files.items():
                # Create any necessary subdirectories
                dir_path = os.path.dirname(filepath)
                if dir_path:
                    sandbox.files.write(dir_path, "")

                # Write the file
                # asyncio.run(sandbox.files.write(filepath, content))
                sandbox.files.write(filepath, content)

            # Install dependencies if package.json exists
            if "package.json" in code_files:
                sandbox.commands.run("npm install")

            # Install TypeScript globally if any .ts files
            if any(f.endswith(".ts") for f in code_files.keys()):
                sandbox.commands.run("npm install -g typescript")
                # Compile TypeScript files
                ts_files = [f for f in code_files.keys() if f.endswith(".ts")]
                if ts_files:
                    sandbox.commands.run("tsc " + " ".join(ts_files))

            # Execute the provided command
            result = sandbox.commands.run(execution_command)

        except Exception as e:
            logging.error(f"E2B execution error: {e}")
            traceback.print_exc()
            result = CommandResult(stdout="", stderr=str(e), exit_code=1, error=str(e))

        sandbox.kill()
        return [], result

    def create_github_pr(
        self,
        code_string: str,
        repo_name: str,
        title: str,
        body: str,
        commit_msg: str,
        branch_name: str,
    ) -> str:
        """
        Creates a PR on GitHub with example code

        Args:
            code_string: Example code in format from execute_creation.txt
            repo_name: Target repository name (format: owner/repo)
            title: Title of the PR
            body: Body of the PR
            commit_msg: Commit message for the PR
            branch_name: Name of the branch to create the PR on
        Returns:
            PR URL if successful, error message if not
        """
        try:
            # Parse files from code string
            files = self.parse_example_files(code_string)
            if not files:
                return "Error: No valid files found in code string"

            # Get default branch
            url = f"{GITHUB_API_BASE}/repos/{repo_name}"
            response = requests.get(url, headers=self.github_headers)
            response.raise_for_status()
            repo_data = response.json()
            base_branch = repo_data["default_branch"]

            # Get base branch SHA
            url = f"{GITHUB_API_BASE}/repos/{repo_name}/git/refs/heads/{base_branch}"
            response = requests.get(url, headers=self.github_headers)
            response.raise_for_status()
            base_sha = response.json()["object"]["sha"]

            # Create new branch
            url = f"{GITHUB_API_BASE}/repos/{repo_name}/git/refs"
            payload = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}
            response = requests.post(url, headers=self.github_headers, json=payload)
            response.raise_for_status()

            # Create/update files in new branch
            # Create a tree with all file changes
            tree_items = []
            for file_path, content in files.items():
                # Create a blob for each file
                url = f"{GITHUB_API_BASE}/repos/{repo_name}/git/blobs"
                blob_payload = {
                    "content": content,
                    "encoding": "utf-8"
                }
                blob_response = requests.post(url, headers=self.github_headers, json=blob_payload)
                blob_response.raise_for_status()
                blob_sha = blob_response.json()["sha"]

                # Add file to tree
                tree_items.append({
                    "path": file_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                })

            # Create a tree with all changes
            url = f"{GITHUB_API_BASE}/repos/{repo_name}/git/trees"
            tree_payload = {
                "base_tree": base_sha,
                "tree": tree_items
            }
            tree_response = requests.post(url, headers=self.github_headers, json=tree_payload)
            tree_response.raise_for_status()
            new_tree_sha = tree_response.json()["sha"]

            # Create a commit with the new tree
            url = f"{GITHUB_API_BASE}/repos/{repo_name}/git/commits"
            commit_payload = {
                "message": commit_msg,
                "tree": new_tree_sha,
                "parents": [base_sha]
            }
            commit_response = requests.post(url, headers=self.github_headers, json=commit_payload)
            commit_response.raise_for_status()
            new_commit_sha = commit_response.json()["sha"]

            # Update branch reference to point to new commit
            url = f"{GITHUB_API_BASE}/repos/{repo_name}/git/refs/heads/{branch_name}"
            ref_payload = {"sha": new_commit_sha}
            ref_response = requests.patch(url, headers=self.github_headers, json=ref_payload)
            ref_response.raise_for_status()

            # Create PR
            url = f"{GITHUB_API_BASE}/repos/{repo_name}/pulls"
            payload = {
                "title": title,
                "body": body,
                "head": branch_name,
                "base": base_branch,
            }
            response = requests.post(url, headers=self.github_headers, json=payload)
            response.raise_for_status()
            pr_data = response.json()

            return pr_data["html_url"]

        except Exception as e:
            traceback.print_exc()
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
            # Remove fpath_ prefix from the file path
            file_path = match.group(1).replace("fpath_", "")
            content = match.group(2)
            files[file_path] = content.strip()

        return files
