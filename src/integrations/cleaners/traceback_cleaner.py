from src.integrations.cleaners.base_cleaner import BaseCleaner
from src.storage.vector import VectorDB
from pydantic import BaseModel
from typing import List

class TracebackStep(BaseModel):
    """
    A step in the traceback
    """
    file: str
    code: str

class TracebackCleaner(BaseCleaner):
    """
    Cleans a traceback by removing unwanted elements and normalizing whitespace.
    """
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db

    def __get_err_fpaths(self, tb: str) -> List[str]:
        """
        Get all file paths mentioned in the traceback.

        Args:
            repo_name (str): The name of the repository
            tb (str): The traceback to get file paths from

        Returns:
            List[str]: The file paths mentioned in the traceback
        """
        file_paths = []
        for line in tb.splitlines():
            if line.startswith("  File "):
                file_path = line.split(",")[0].split(" ")[1].strip('"')
                file_paths.append(file_path)

        return file_paths
        
    def __get_chunks_from_traceback(self, traceback: str) -> List[TracebackStep]:
        """
        Get the code chunks from a traceback into traceback objects.

        Args:
            repo_name (str): The name of the repository
            traceback (str): The traceback to get code chunks from

        Returns:
            List[TracebackStep]: The code chunks from the traceback
        """
        # 1. Get all file paths mentioned in the traceback
        file_paths = self.__get_err_fpaths(traceback)

        # 2. for each file path, get try to get the relevant CodePage object from the vector db
        steps = []
        for file_path in file_paths:
            code_page = self.vector_db.get_code_file(file_path)

            step = TracebackStep(file=code_page.file_path, code=code_page.content)
            steps.append(step)
        
        # 3. return the list of traceback steps ordered by the traceback
        return steps

    def clean(self, traceback: str) -> List[TracebackStep]:
        """
        Takes a traceback, and returns a set of structured traceback objects
        """
        return self.__get_chunks_from_traceback(traceback)
