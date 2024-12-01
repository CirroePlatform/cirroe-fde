from scripts.solve_oss_ghub_issues import setup_all_kbs_with_repo
from src.storage.supa import SupaClient
from test.eval_agent import Orchestrator
from src.core.event.poll import poll_for_issues

from uuid import UUID
import asyncio
from src.core.event.user_actions.handle_discord_message import HandleDiscordMessage
from src.model.issue import DiscordMessage
from include.constants import MEM0AI_ORG_ID, REPO_NAME, GRAVITL_ORG_ID, MITO_DS_ORG_ID, FLOWISE_ORG_ID, ARROYO_ORG_ID


def evaluate(
    org_id: UUID,
    org_name: str,
    repo_name: str,
    test_train_ratio: float = 0.2,
    enable_labels: bool = True,
):
    orchestrator = Orchestrator(
        org_id,
        org_name,
        repo_name,
        test_train_ratio=test_train_ratio,
        enable_labels=enable_labels,
    )
    orchestrator.evaluate()


def index(org_id: UUID, org_name: str, repo_name: str, docu_url: str):
    asyncio.run(setup_all_kbs_with_repo(org_id, org_name, repo_name, docu_url))

def handle_discord_message(inbound_message: str, org_id: UUID):
    disc_handler = HandleDiscordMessage(org_id)

    message = DiscordMessage(
        author="aswanth",
        content=inbound_message,
        channel_id="123",
    )
    
    response = disc_handler.handle_discord_message(message)
    print(response)

    return response

def poll_wrapper():
    orgs_to_tickets = {
        GRAVITL_ORG_ID: [3020, 3019],
        MITO_DS_ORG_ID: [1332],
        FLOWISE_ORG_ID: [3577, 2592],
        ARROYO_ORG_ID: [756, 728],
    }

    for org in orgs_to_tickets:
        # 1. get repo info
        supa = SupaClient(org)
        repo_info = supa.get_user_data(
            "org_name", REPO_NAME, "repo_url", "docu_url", debug=True
        )

        # 2. evaluate and save results
        # evaluate(org, repo_info["org_name"], repo_info[REPO_NAME], test_train_ratio=0.2, enable_labels=True)

        poll_for_issues(org, repo_info[REPO_NAME], True, ticket_numbers=[str(ticket) for ticket in orgs_to_tickets[org]])
    

if __name__ == "__main__":
    disc_msg = """
Hi everyone,

I’m working with a Sequential Autogen agent flow for a text-to-SQL LLM chatbot use case, and I need to store chat history for the duration of a single user-chat session. (store memory to maintain the context throughout one chat session).

How to use Mem0 for the same , kindly please give suggestions.

Here’s the detailed Autogen Agent workflow I’m using:
1.User Proxy Agent: Takes the user question from the frontend.
2.Assistant: Understands the use case and prepares a task plan to solve the query.
3.Assistant: Retrieves the DDL from the vector database based on the user query (text question from the User Proxy Agent).
4.Assistant: Uses the retrieved DDL to generate the SQL query.

Also ,If anyone has implemented this or , could you share any code repositories or sample code to refer to?
Looking forward to your suggestions !
    """

    disc_msg = DiscordMessage(content=disc_msg, author="Priya Issar", channel_id="123", message_id="123")
    response = HandleDiscordMessage(MEM0AI_ORG_ID).handle_discord_message(disc_msg)

    print(f"```markdown\n{response}\n```")