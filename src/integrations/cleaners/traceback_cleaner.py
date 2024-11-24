from src.integrations.cleaners.base_cleaner import BaseCleaner
from src.storage.vector import VectorDB
from src.model.code import CodePage
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

            line = line.lstrip().rstrip()
            if line.startswith("File"):
                splitted = line.split(",")  # Note: line number is usually at the idx 1

                fp1 = splitted[0]
                fp2 = fp1.split(" ")[1].strip('"')
                fp2 = fp2.split("\\")[-1]  # removing the leading path

                file_paths.append(fp2)

        return file_paths

    def __get_code_pages_from_file_paths(self, file_paths: List[str]) -> List[CodePage]:
        """
        Get the code pages from a list of file paths.

        TODO: Right now, we haven't tested the positive case, so not sure if this will work.
        """
        pages = self.vector_db.get_code_pages(filename_filter=file_paths)

        return pages

    def __get_chunks_from_traceback(self, tb: str) -> List[TracebackStep]:
        """
        Get the code chunks from a traceback into traceback objects.

        Args:
            repo_name (str): The name of the repository
            traceback (str): The traceback to get code chunks from

        Returns:
            List[TracebackStep]: The code chunks from the traceback
        """
        # 1. Get all file paths mentioned in the traceback
        file_paths = self.__get_err_fpaths(tb)

        # 2. for each file path, get try to get the relevant CodePage object from the vector db
        steps = []
        for file_path in file_paths:

            code_pages = self.__get_code_pages_from_file_paths(file_path)
            for code_page in code_pages:
                step = TracebackStep(file=code_page.file_path, code=code_page.content)
                steps.append(step)

        # 3. return the list of traceback steps ordered by the traceback
        return steps

    def clean(self, tb: str) -> List[TracebackStep]:
        """
        Takes a traceback, and returns a set of structured traceback objects
        """
        return self.__get_chunks_from_traceback(tb)
