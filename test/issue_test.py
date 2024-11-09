import logging
from src.model.issue import Issue
from uuid import uuid4, UUID
import asyncio
from src.integrations.kbs.issue_kb import IssueKnowledgeBase


org_id = UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1")
issue_kb = IssueKnowledgeBase(org_id)


async def test_issue_kb():
    # Test indexing a single ticket
    issue_id = UUID("e166e523-c217-49d1-b7a8-b759a01ee310")
    test_ticket = Issue(
        primary_key=str(issue_id),
        description="Having issues with multimodal queries in production",
        comments={
            "Jacob": "Have you checked the model configuration?",
            "Tom @ Cirroe": "Yes, config looks correct but still failing",
        },
        org_id=org_id,
    )
    success = await issue_kb.index(test_ticket)
    logging.info(f"Index single ticket result: {success}")

    # Test querying indexed tickets
    query = "multimodal query issues"
    results = await issue_kb.query(query, limit=2)
    logging.info("\nQuery results:")
    for result in results:
        logging.info(f"\nSource: {result.source}")
        logging.info(f"Content: {result.content}")
        logging.info(f"Score: {result.relevance_score}")

    # Test indexing multiple tickets
    test_tickets = [
        Issue(
            primary_key=str(uuid4()),
            description="Need help configuring model parameters",
            comments={
                "Tom @ Cirroe": "Which parameters are you trying to set?",
                "Jacob": "The temperature and max tokens",
            },
            org_id=org_id,
        ),
        Issue(
            primary_key=str(uuid4()),
            description="API returning 500 error on image uploads",
            comments={
                "Tom @ Cirroe": "Is this happening for all image types?",
                "Jacob": "Only for PNG files over 5MB",
            },
            org_id=org_id,
        ),
    ]

    for ticket in test_tickets:
        await issue_kb.index(ticket)

    # Test broader query
    query = "configuration problems"
    results = await issue_kb.query(query, limit=3)
    logging.info("\nBroader query results:")
    for result in results:
        logging.info(f"\nSource: {result.source}")
        logging.info(f"Content: {result.content}")
        logging.info(f"Score: {result.score}")


# Run tests
asyncio.run(test_issue_kb())
