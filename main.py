from src.sutils.handle_issue_action import HandleIssueAction
from src.model.issue import Issue, Comment

action = HandleIssueAction(1)

comments=[Comment(requestor_id=1, content="b", ts=1)]
print(action.handle_request(Issue(tid=1, problem_description="b", comments=comments)))