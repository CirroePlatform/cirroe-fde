from typing import List
from uuid import UUID

from src.storage.vector import VectorDB

from src.model.issue import Issue
from src.model.runbook import Runbook

SIM_THRESHOLD = 0.6


class IssueClassifier:
    """
    A class to help classify runbooks based on inbound issues.
    """

    def __init__(self, vector_db: VectorDB) -> None:
        self.vector_db = vector_db

    def classify(self, issue: Issue, k: int = 3) -> List[Runbook]:
        """
        Returns a list of runbook ids sorted from most to least
        relevant.
        """
        # 1. Vectorize the issue description
        issue_vector = self.vector_db.embed_issue(issue)

        # 2. run top k on the issue against the runbook rb
        vectors_and_sims = self.vector_db.get_top_k(issue_vector, k)

        # 3. get top k above some threshold, and return a list of runbooks, sorted from
        # most to least useful.
        rv = []
        for rb, sim in vectors_and_sims:
            if sim >= SIM_THRESHOLD:
                rv.append(rb)

        if len(rv) != 0:
            return rv

        # 4. TODO Uh oh, need to alert a human here.
