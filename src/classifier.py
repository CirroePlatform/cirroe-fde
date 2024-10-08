from src.model.issue import Issue, IssueType
from typeguard import typechecked

@typechecked
class Classifier:
    """
    Issue classifier. Should be able to decipher "dangerous" issues, or route to relevant teams
    """
    def __init__(self) -> None:
        pass

    def is_dangerous(self, issue: Issue) -> bool:
        """
        Returns whether the provided issue is 
        dangerous or not. Only called on issue creation.
        """
        return True

    def get_type(self, issue: Issue) -> IssueType:
        """
        Gets issue type of a provided issue.
        """
        return IssueType(name="nan")
