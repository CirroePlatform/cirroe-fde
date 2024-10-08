from abc import ABC, abstractmethod


class AbstractLLM(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def query(self, prompt: str) -> str:
        pass


def get_navigation_string(heuristic: str, input_str: str, category: str) -> str:
    """Returns a crafted heuristic prompt based on the provided args"""

    return f"""
        resume: {input_str}

        job requirements: {heuristic}

        Question: Out of the provided job description and resume, respond with 'accept' if 
        the resume fullfills over half of the requirements of the job description. Respond with 
        'reject' if it does not. Provide a reasoning for your response. 

        Make a decision based upon the provided information alone. If there are any substantial
        gaps or missing portions of the resume related to the heuristic, the candidate should be 
        rejected.

        Answer:
        """


# You have a candidate and a label. On the bases of the following heuristcs
#         here: {heuristic} decide whether the following candidate: {input_str} should be accepted for
#         the role of {category}. When providing a reasoning, only reference the specific heuristics provided,
#         all your lines of reasoning should be relevant to the provided heuristic.

#         An accepted candidate should not just fit the role, but also go above and beyond in demonstrating that
#         they can excel in the role. They should have yielded quantifiable results that pertain to the provided
#         heursitic, and if they do not, they should be rejected. You should only accept a candidate that fullfills
#         a majority of the heuristics.

#         Specifically mention 'reject' or 'accept' depending on your decision
#         """
