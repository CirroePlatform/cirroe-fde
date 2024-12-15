from scripts.solve_oss_ghub_issues import setup_all_kbs_with_repo
from scripts.oss_ghub_issue_analysis import (
    analyze_repos,
    bulk_extract_github_links,
    analyze_github_issues,
)
from src.storage.supa import SupaClient
from test.eval_agent import Orchestrator
from src.core.event.poll import poll_for_issues, bot, disc_token

from uuid import UUID
import asyncio
from src.core.event.user_actions.handle_discord_message import DiscordMessageHandler
from src.model.issue import DiscordMessage
from include.constants import (
    MEM0AI_ORG_ID,
    REPO_NAME,
    TRIGGER_ORG_ID,
    GRAVITL_ORG_ID,
    MITO_DS_ORG_ID,
    FLOWISE_ORG_ID,
    VIDEO_DB_ORG_ID,
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
    disc_handler = DiscordMessageHandler(org_id)

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
        # FLOWISE_ORG_ID: [3577],
        # ARROYO_ORG_ID: [756, 728],
        MEM0AI_ORG_ID: [2079],
        # TRIGGER_ORG_ID: [1490],
        # VIDEO_DB_ORG_ID: [65],
    }

    for org in orgs_to_tickets:
        # 1. get repo info
        supa = SupaClient(org)
        repo_info = supa.get_user_data(
            "org_name", REPO_NAME, "repo_url", "docu_url", debug=True
        )

        # 2. evaluate and save results
        # evaluate(org, repo_info["org_name"], repo_info[REPO_NAME], test_train_ratio=0.2, enable_labels=True)

        index(org, repo_info["org_name"], repo_info[REPO_NAME], repo_info["docu_url"])
        # poll_for_issues(
        #     org,
        #     repo_info[REPO_NAME],
        #     True,
        #     ticket_numbers=[str(ticket) for ticket in orgs_to_tickets[org]],
        # )


def discord_wrapper():
    disc_msg = """
Hey, I am using crew ai to build agents for customers, Every customer has some sort of preference in having a particular task done, I have a txt file for the same for every customer, how can i put this txt file or extract data from it and put it in memory. Because all the examples of mem0 contains adding memory in the format of messages object. But i have as a preference of user as a blob of text.
    """
    from rich.console import Console
    from rich.markdown import Markdown

    disc_msg = DiscordMessage(
        content=disc_msg, author="kanika", channel_id="123", message_id="123"
    )
    response = DiscordMessageHandler(MEM0AI_ORG_ID).handle_discord_message(
        disc_msg, max_tool_calls=5
    )

    console = Console()
    md = Markdown(response["response"])
    console.print(md)

    print(f"Raw: {response}")


def discord_bot():
    bot.run(disc_token)


def collect_data_for_links():
    links = [
        "https://lyteshot.com/",
        "rule4.com",
        "liblab.com",
        "erxes.io",
        "infisical.com",
        "phylum.io",
        "buoyant.io",
        "unskript.com",
        "culturesqueapp.com",
        "freestaq.com",
        "ceramic.network",
        "pascalemarill.com",
        "hexabot.ai",
        "aguaclarallc.com",
        "resources.whitesourcesoftware.com",
        "opensearchserver.com",
        "chainstone.com",
        "ethyca.com",
        "formbricks.com",
        "tobikodata.com",
        "sandworm.dev",
        "openweaver.com",
        "beekeeperstudio.io",
        "bloq.com",
        "theninehertz.com",
        "fairwaves.co",
        "openteams.com",
        "gatesdefense.com",
        "ubisense.net",
        "layerware.com",
        "grai.io",
        "https://www.pavconllc.com/",
        "3dponics.com",
        "newamerica.org",
        "solonlabs.net",
        "zededa.com",
        "prefect.io",
        "catena.xyz",
        "paladincloud.io",
        "mage.ai",
        "heartex.com",
        "crate.io",
        "entando.com",
        "mattermost.com",
        "akash.network",
        "harness.io",
        "https://www.getdbt.com/",
        "https://graylog.org/",
        "https://www.acquia.com/",
        "https://www.stacks.co/",
        "https://cratedb.com/",
        "https://grafana.com/",
        "https://posthog.com/",
        "socket.dev",
        "https://appwrite.io/",
        "sentry.io",
    ]
    bulk_extract_github_links(links)


if __name__ == "__main__":
    poll_wrapper()
    discord_wrapper()
    # print(analyze_github_issues(UUID("123e4567-e89b-12d3-a456-426614174026")))
