from scripts.solve_oss_ghub_issues import setup_all_kbs_with_repo
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
    GRAVITL_ORG_ID,
    MITO_DS_ORG_ID,
    FLOWISE_ORG_ID,
    ARROYO_ORG_ID,
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
        # MITO_DS_ORG_ID: [1332],
        # FLOWISE_ORG_ID: [3615],
        # ARROYO_ORG_ID: [756, 728],
    }

    for org in orgs_to_tickets:
        # 1. get repo info
        supa = SupaClient(org)
        repo_info = supa.get_user_data(
            "org_name", REPO_NAME, "repo_url", "docu_url", debug=True
        )

        # 2. evaluate and save results
        # evaluate(org, repo_info["org_name"], repo_info[REPO_NAME], test_train_ratio=0.2, enable_labels=True)

        # poll_for_issues(org, repo_info[REPO_NAME], True, ticket_numbers=[str(ticket) for ticket in orgs_to_tickets[org]])
        index(org, repo_info["org_name"], repo_info[REPO_NAME], repo_info["docu_url"])


def discord_wrapper():
    disc_msg = """
octocat: Hi i got this issues when checkout the repos and build from master and v0.12. previously i install arroyo via scripts. then uninstall those . is there something that cause this? @Micah Wylde 

2024-11-29T14:23:47.699412Z  INFO arroyo_controller::states::scheduling: starting execution on worker job_id="job_SzD0oomo4y" worker_id=101
2024-11-29T14:23:54.007828Z ERROR arroyo_controller::states::scheduling: failed to start execution on worker job_id="job_SzD0oomo4y" worker_id=101 attempt=0 error="Status { code: Unknown, message: \"transport error\", source: Some(tonic::transport::Error(Transport, hyper::Error(Io, Custom { kind: BrokenPipe, error: \"stream closed because of a broken pipe\" }))) }"
2024-11-29T14:24:05.904961Z ERROR arroyo_controller::states::scheduling: failed to start execution on worker job_id="job_SzD0oomo4y" worker_id=101 attempt=1 error="Status { code: Unknown, message: \"transport error\", source: Some(tonic::transport::Error(Transport, hyper::Error(Io, Custom { kind: BrokenPipe, error: \"stream closed because of a broken pipe\" }))) }"
2024-11-29T14:24:19.277173Z ERROR arroyo_controller::states::scheduling: failed to start execution on worker job_id="job_SzD0oomo4y" worker_id=101 attempt=2 error="Status { code: Unknown, message: \"transport error\", source: Some(tonic::transport::Error(Transport, hyper::Error(Io, Custom { kind: BrokenPipe, error: \"stream closed because of a broken pipe\" }))) }"
    
ecararra: I encountered the same error on macOS. To resolve it, I had to add the Arroyo binary path to the firewall allow list.
    """
    from rich.console import Console
    from rich.markdown import Markdown

    disc_msg = DiscordMessage(
        content=disc_msg, author="neotherack", channel_id="123", message_id="123"
    )
    response = HandleDiscordMessage(ARROYO_ORG_ID).handle_discord_message(disc_msg)

    console = Console()
    md = Markdown(response["response"])
    console.print(md)

    print(f"Raw: {response}")

def discord_bot():
    bot.run(disc_token)

if __name__ == "__main__":
    discord_bot()
