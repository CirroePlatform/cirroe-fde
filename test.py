from src.core.handle_issue import debug_issue, OpenIssueRequest
from src.model.issue import Issue
from uuid import uuid4, UUID
import asyncio
from src.integrations.issue_kb import IssueKnowledgeBase


org_id=UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1")
issue_kb = IssueKnowledgeBase(org_id)

async def test_issue_kb():
    # Test indexing a single ticket
    issue_id = UUID("e166e523-c217-49d1-b7a8-b759a01ee310")
    test_ticket = Issue(
        primary_key=issue_id,
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
        print(f"Score: {result.relevance_score}")

    # Test indexing multiple tickets
    test_tickets = [
        Issue(
            primary_key=uuid4(),
            problem_description="Need help configuring model parameters",
            comments={"Tom @ Cirroe": "Which parameters are you trying to set?", "Jacob": "The temperature and max tokens"}
        ),
        Issue(
            primary_key=uuid4(),
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
