from src.core.handle_issue import debug_issue, OpenIssueRequest
from src.model.issue import Issue
from uuid import uuid4
import asyncio
from src.integrations.issue_kb import IssueKnowledgeBase


org_id="90a11a74-cfcf-4988-b97a-c4ab21edd0a1"
issue_kb = IssueKnowledgeBase(org_id)

issue_req = OpenIssueRequest(
    requestor_id=uuid4(),
    issue=Issue(
        tid=uuid4(),
        problem_description="Can't seem to figure out how to query Hermes for multimodal support. Can someone help?",
        comments={},
    ),
)


async def test_issue_kb():
    # Test indexing a single ticket
    test_ticket = Issue(
        tid=uuid4(),
        problem_description="Having issues with multimodal queries in production",
        comments={"Jacob": "Have you checked the model configuration?", "Tom @ Cirroe": "Yes, config looks correct but still failing"}
    )
    success = await issue_kb.index(test_ticket)
    print(f"Index single ticket result: {success}")

    # Test querying indexed tickets
    query = "multimodal query issues"
    results = await issue_kb.query(query, limit=2)
    print("\nQuery results:")
    for result in results:
        print(f"\nSource: {result.source}")
        print(f"Content: {result.content}")
        print(f"Score: {result.score}")

    # Test indexing multiple tickets
    test_tickets = [
        Issue(
            tid=uuid4(),
            problem_description="Need help configuring model parameters",
            comments={"Tom @ Cirroe": "Which parameters are you trying to set?", "Jacob": "The temperature and max tokens"}
        ),
        Issue(
            tid=uuid4(),
            problem_description="API returning 500 error on image uploads",
            comments={"Tom @ Cirroe": "Is this happening for all image types?", "Jacob": "Only for PNG files over 5MB"}
        )
    ]
    
    for ticket in test_tickets:
        await issue_kb.index(ticket)
    
    # Test broader query
    query = "configuration problems"
    results = await issue_kb.query(query, limit=3)
    print("\nBroader query results:")
    for result in results:
        print(f"\nSource: {result.source}")
        print(f"Content: {result.content}")
        print(f"Score: {result.score}")

# Run tests
asyncio.run(test_issue_kb())
