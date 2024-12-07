from scripts.solve_oss_ghub_issues import setup_all_kbs_with_repo
from scripts.oss_ghub_issue_analysis import analyze_repos
from src.storage.supa import SupaClient
from test.eval_agent import Orchestrator
from src.core.event.poll import poll_for_issues, bot, disc_token

from uuid import UUID
import asyncio
from src.core.event.user_actions.handle_discord_message import HandleDiscordMessage
from src.model.issue import DiscordMessage
from include.constants import (
    MEM0AI_ORG_ID,
    REPO_NAME,
    TRIGGER_ORG_ID,
    GRAVITL_ORG_ID,
    MITO_DS_ORG_ID,
    FLOWISE_ORG_ID,
    ARROYO_ORG_ID,
    PREDIBASE_ORG_ID,
)


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
        # GRAVITL_ORG_ID: [3020, 3019],
        MITO_DS_ORG_ID: [1332],
        # FLOWISE_ORG_ID: [3577],
        # ARROYO_ORG_ID: [756, 728],
        # MEM0AI_ORG_ID: [2069],
        # TRIGGER_ORG_ID: [1490],
    }

    for org in orgs_to_tickets:
        # 1. get repo info
        supa = SupaClient(org)
        repo_info = supa.get_user_data(
            "org_name", REPO_NAME, "repo_url", "docu_url", debug=True
        )

        # 2. evaluate and save results
        # evaluate(org, repo_info["org_name"], repo_info[REPO_NAME], test_train_ratio=0.2, enable_labels=True)

        # index(org, repo_info["org_name"], repo_info[REPO_NAME], repo_info["docu_url"])
        poll_for_issues(
            org,
            repo_info[REPO_NAME],
            True,
            ticket_numbers=[str(ticket) for ticket in orgs_to_tickets[org]],
        )


def discord_wrapper():
    disc_msg = """
Good evening,

I've been trying to get your service to work for several days now, but it only works in dev.

From what I understand, the GitHub action builds a Docker image, which is hosted on ghcr.io for my part. The rest goes well since the "deployments" page on the Trigger.dev interface in self host shows me that the deployment is complete (in green), but the queues/jobs are not processed, even if I restart the task.

I tried to host the service on Coolify, even on another VPS completely empty of service (reinstallation from scratch), and even locally, result: there are websocket errors everywhere in the logs.

Please review your documentation which seems a bit empty for novices like me in the Docker environment.

Docker Provider log for exemple:
2024-12-06T22:41:17.368219680Z {"timestamp":"2024-12-06T22:41:17.368Z","message":"disconnect","$name":"socket-shared-queue","$level":"info","namespace":"shared-queue","host":"webapp","port":3000,"secure":false,"reason":"transport close","description":{"description":"websocket connection closed","context":{}}}


Thanks to help me.

Maxence.
    """
    from rich.console import Console
    from rich.markdown import Markdown

    disc_msg = DiscordMessage(
        content=disc_msg, author="Priya", channel_id="123", message_id="123"
    )
    response = HandleDiscordMessage(TRIGGER_ORG_ID).handle_discord_message(
        disc_msg, max_tool_calls=5
    )

    console = Console()
    md = Markdown(response["response"])
    console.print(md)

    print(f"Raw: {response}")

def discord_bot():
    bot.run(disc_token)

if __name__ == "__main__":
    # poll_wrapper()
    analyze_repos()
