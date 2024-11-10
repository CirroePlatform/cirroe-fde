from uuid import UUID
import anthropic
import logging
import random
from typing import List, Set
from src.model.issue import Issue, OpenIssueRequest

from src.core.event.handle_issue import debug_issue
from src.integrations.kbs.github_kb import GithubIntegration
from src.storage.vector import VectorDB

from include.constants import DEFAULT_TEST_TRAIN_RATIO, EVAL_AGENT_RESPONSE_PROMPT, MODEL_HEAVY

class TestOrchestrator:
    """
    Orchestrates the testing of the agent on a given org.
    """
    def __init__(self, org_id: UUID, test_repo_name: str,test_train_ratio: float = DEFAULT_TEST_TRAIN_RATIO):
        self.org_id = org_id
        self.test_train_ratio = test_train_ratio
        self.test_repo_name = test_repo_name
        
        self.vector_db = VectorDB(org_id)
        self.github_kb = GithubIntegration(org_id)
    
    def __get_closed_or_solved_issues(self) -> List[Issue]:
        """
        Get all closed or solved issues based on the org_id.
        """
        issues = self.github_kb.get_all_issues_json(self.test_repo_name, "closed")
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

    def setup_test_train_issues_splits(self) -> Set[Issue]:
        """
        The issue knowledgebase is a bit different, because we are evaluating inbound issues, we need to make sure the knowledgebase
        isn't indexed with any issues from the org in our test set.
        
        Therefore, if the issue kb is already indexed, we consider the non-indexed, solved issues in our test set. Else, we randomly split the
        issues into training and testing with the split_issues method.
        
        returns the test set.
        """
        # 1. Pull all issues from the git repo that are closed or resolved.
        issues = set(self.__get_closed_or_solved_issues())
        num_solved_or_closed_issues = len(issues)
        test_set: Set[Issue]

        # 2. Check and see how many issues are already indexed in the vector db.
        indexed_issues = set(self.vector_db.get_all_issues())
        num_indexed_issues = len(indexed_issues)
        
        # 3. If nun_indexed_in_vector_db / total closed or resolved issues in repo < 1 - test_train_ratio, we need to randomly sample issues 
        # from the total issues that haven't been indexed for the test set, and index them until we reach the desired test and train ratio.
        # We should never exceed the ratio, because new tickets will be closed and solved in these repos.
        if num_indexed_issues / num_solved_or_closed_issues < (1 - self.test_train_ratio): # TODO Untested
            unindexed_issues = issues - indexed_issues
            test_set = unindexed_issues

            # 3.a Index all the unindexed issues until we reach the desired test and train ratio.
            # Convert to list for random sampling
            unindexed_list = list(unindexed_issues)
            random.shuffle(unindexed_list)
            
            for issue in unindexed_list:
                self.vector_db.add_issue(issue)
                test_set.remove(issue)
                
                num_indexed_issues += 1
                if num_indexed_issues / num_solved_or_closed_issues >= (1 - self.test_train_ratio):
                    break
        else:
            test_set = issues - indexed_issues

        return test_set

    def evaluate(self):
        """
        Main entry point to evaluate our agent on a specific org's issues.
        """
        # 1. Setup the test and train issues    
        test_issues = self.setup_test_train_issues_splits()

        # 2. Evaluate the agent on the test issues
        evaluator = Evaluator(self.org_id, test_issues, self.test_train_ratio)
        evaluator.evaluate()

class Evaluator:
    """
    A class that evaluates the performance of the agent on one org.
    """

    def __init__(self, org_id: UUID, test_issues: Set[Issue], test_train_ratio: float = 0.2):
        self.org_id = org_id
        self.test_issues = test_issues
        self.test_train_ratio = test_train_ratio
        
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
            {"role": "user", "content": f"issue: {issue.description}, comments: {issue.comments}, response: {response}"},
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

            response = debug_issue(OpenIssueRequest(requestor_id=self.org_id, issue=issue))
            
            # Add the comments back to the issue object for evaluation
            issue.comments = comments
            total_success += self.evaluate_agent_response(issue, response)

        logging.info(f"Evaluation complete. test/train ratio: {self.test_train_ratio}. Total issues: {total_issues}, Total success: {total_success}, Success rate: {total_success / total_issues}.")
        