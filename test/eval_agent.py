from uuid import UUID
import anthropic
import json
import logging
import os
import random
from typing import List, Set
from src.model.issue import Issue, OpenIssueRequest

from src.core.event.handle_issue import debug_issue
from src.integrations.kbs.github_kb import GithubIntegration, Repository
from src.storage.vector import VectorDB

from include.constants import (
    DEFAULT_TEST_TRAIN_RATIO,
    EVAL_AGENT_RESPONSE_PROMPT,
    MODEL_HEAVY,
    CACHE_DIR,
)


class Orchestrator:
    """
    Orchestrates the testing of the agent on a given org.
    """

    def __init__(
        self,
        org_id: UUID,
        org_name: str,
        test_repo_name: str,
        test_train_ratio: float = DEFAULT_TEST_TRAIN_RATIO,
    ):
        self.org_id = org_id
        self.org_name = org_name
        self.test_train_ratio = test_train_ratio
        self.test_repo_name = test_repo_name
        self.repos = [Repository(repository=f"{self.org_name}/{self.test_repo_name}", branch="main", remote="github")]

        self.vector_db = VectorDB(org_id)
        self.github_kb = GithubIntegration(org_id, org_name, self.repos)

    def __get_closed_or_solved_issues(self) -> List[Issue]:
        """
        Get all closed or solved issues based on the org_id.
        """
        # Cached data, makes it such that new closed issues aren't considered.
        cache_file = os.path.join(CACHE_DIR, f"{self.test_repo_name}_closed_issues.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf8") as fp:
                issues = json.load(fp)
        else:
            issues = self.github_kb.get_all_issues_json(self.test_repo_name, "closed")
            with open(cache_file, "w", encoding="utf8") as fp:
                json.dump(issues, fp)
        solved_or_closed_issues = []

        for issue in issues:
            comments = {}
            for comment in issue["comments"]:
                comments[comment["user"]["login"]] = comment["body"]

            solved_or_closed_issues.append(
                Issue(
                    primary_key=str(issue["id"]),
                    description=f"title: {issue['title']}, description: {issue['body']}",
                    comments=comments,
                    org_id=self.org_id,
                )
            )

        return solved_or_closed_issues

    def setup_test_train_issues_splits(self) -> List[Issue]:
        """
        The issue knowledgebase is a bit different, because we are evaluating inbound issues, we need to make sure the knowledgebase
        isn't indexed with any issues from the org in our test set.

        Therefore, if the issue kb is already indexed, we consider the non-indexed, solved issues in our test set. Else, we randomly split the
        issues into training and testing with the split_issues method.

        returns the test set. As of now we sacrifice runtime for memory because sets cant hash issues.
        """
        # 1. Pull all issues from the git repo that are closed or resolved.
        logging.info(f"Pulling all closed or resolved issues from {self.test_repo_name}...")
        issues = self.__get_closed_or_solved_issues()
        total_issues_ids = set([issue.primary_key for issue in issues])
        assert len(total_issues_ids) == len(issues)
        num_solved_or_closed_issues = len(total_issues_ids)

        # 2. Check and see how many issues are already indexed in the vector db.
        logging.info(f"Checking how many issues are already indexed in the vector db...")
        indexed_issues = self.vector_db.get_all_issues()
        indexed_issues_ids = set([issue.primary_key for issue in indexed_issues])
        assert len(indexed_issues_ids) == len(indexed_issues)
        num_indexed_issues = len(indexed_issues_ids)

        test_set: List[Issue] = []
        # 3. If nun_indexed_in_vector_db / total closed or resolved issues in repo < 1 - test_train_ratio, we need to randomly sample issues
        # from the total issues that haven't been indexed for the test set, and index them until we reach the desired test and train ratio.
        # We should never exceed the ratio, because new tickets will be closed and solved in these repos.
        if num_indexed_issues / num_solved_or_closed_issues < (
            1 - self.test_train_ratio
        ):
            logging.info(f"num indexed issues is too low. current ratio: {num_indexed_issues / num_solved_or_closed_issues}, desired ratio: {1 - self.test_train_ratio}")
            unindexed_list = [issue for issue in issues if issue.primary_key not in indexed_issues_ids]
            test_set = unindexed_list

            # 3.a Index all the unindexed issues until we reach the desired test and train ratio.
            # Convert to list for random sampling
            random.shuffle(unindexed_list)

            logging.info(f"Indexing at most {len(unindexed_list)} issues to reach desired test/train ratio...")
            for issue in unindexed_list:
                self.vector_db.add_issue(issue)
                test_set.append(issue)

                num_indexed_issues += 1
                if num_indexed_issues / num_solved_or_closed_issues >= (
                    1 - self.test_train_ratio
                ):
                    logging.info(f"Reached desired test/train ratio. Indexed {num_indexed_issues} issues out of {num_solved_or_closed_issues} total issues.")
                    break
        else:
            # Technically, we can reach a case where we have more indexed issues than closed or resolved issues.
            # I don't think we should be performing any deletes in this case, maybe it's best to setup a prod and test knowledgebase.
            # test_set = [issue for issue in issues if issue.primary_key not in indexed_issues_ids]
            for issue in issues:
                if issue.primary_key not in indexed_issues_ids:
                    test_set.append(issue)

        return test_set

    def evaluate(self):
        """
        Main entry point to evaluate our agent on a specific org's issues.
        """
        # 1. Setup the test and train issues
        test_issues = self.setup_test_train_issues_splits()
        logging.info(f"Evaluating agent on {len(test_issues)} issues.")

        # 2. Evaluate the agent on the test issues
        evaluator = Evaluator(self.org_id, test_issues, self.repos, self.test_train_ratio)
        evaluator.evaluate()


class Evaluator:
    """
    A class that evaluates the performance of the agent on one org.
    """

    def __init__(
        self, org_id: UUID, test_issues: List[Issue], github_repos: List[Repository], test_train_ratio: float = 0.2
    ):
        self.org_id = org_id
        self.test_issues = test_issues
        self.test_train_ratio = test_train_ratio
        self.github_repos = github_repos
        self.judge_client = anthropic.Anthropic()

    def evaluate_agent_response(self, issue: Issue, response: str) -> bool:
        """
        Evaluate the agent's response to an issue. Returns a boolean value indicating whether the response was correct, uses
        a model judge to evaluate the response against the actual issue comments.
        """
        with open(EVAL_AGENT_RESPONSE_PROMPT, "r", encoding="utf8") as fp:
            sysprompt = fp.read()

        messages = [
            {"role": "system", "content": sysprompt},
            {
                "role": "user",
                "content": f"<issue>{issue.description}</issue>\n<comments>{issue.comments}</comments>\n<agent_response>{response}</agent_response>",
            },
        ]

        response = self.judge_client.messages.create(
            model=MODEL_HEAVY,
            system=sysprompt,
            max_tokens=2048,
            messages=messages,
        )

        return response.content[0].text.lower() == "true"

    def evaluate(self):
        """
        Evaluate the agent on the test set.
        """
        total_issues = len(self.test_issues)
        total_success = 0

        for issue in self.test_issues:
            # Take the comments out of the issue object
            comments = issue.comments
            issue.comments = {}

            response = debug_issue(
                OpenIssueRequest(requestor_id=self.org_id, issue=issue), 
                github_repos=self.github_repos
            )

            # Add the comments back to the issue object for evaluation
            issue.comments = comments
            total_success += self.evaluate_agent_response(issue, response)

        logging.info(
            f"Evaluation complete. test/train ratio: {self.test_train_ratio}. Total issues: {total_issues}, Total success: {total_success}, Success rate: {total_success / total_issues}."
        )
