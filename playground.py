from src.integrations.kbs.github_kb import GithubKnowledgeBase
from scripts.solve_oss_ghub_issues import setup_all_kbs_with_repo
from fastapi import Request
import os
import logging
from scripts.oss_ghub_issue_analysis import (
    analyze_repos,
    bulk_extract_github_links,
    analyze_github_issues,
)
from src.storage.supa import SupaClient
from test.eval_agent import Orchestrator
from src.core.event.poll import poll_for_issues
from src.model.code import CodePage, CodePageType
from typing import List
from uuid import UUID
import asyncio
from src.core.event.tool_actions.handle_discord_message import DiscordMessageHandler
from src.model.issue import DiscordMessage
from include.constants import (
    MEM0AI_ORG_ID,
    REPO_NAME,
    VOYAGE_CODE_EMBED,
    QDRANT_ORG_ID,
    GRAVITL_ORG_ID,
    MITO_DS_ORG_ID,
    FLOWISE_ORG_ID,
    VIDEO_DB_ORG_ID,
    ARROYO_ORG_ID,
    PREDIBASE_ORG_ID,
    CHROMA_ORG_ID,
    FIRECRAWL_ORG_ID,
)

from src.example_creator.sandbox import Sandbox
from src.core.tools import SearchTools

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
        # MEM0AI_ORG_ID: [2079],
        # CHROMA_ORG_ID: [2571],
        # ARROYO_ORG_ID: [3265, 3292],
        # QDRANT_ORG_ID: [],
        FIRECRAWL_ORG_ID: [2571],
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
    disc_msg = """"""
    from rich.console import Console
    from rich.markdown import Markdown

    disc_msg = DiscordMessage(content=disc_msg, author="juan", attachments=[])
    response = DiscordMessageHandler(QDRANT_ORG_ID).handle_discord_message(
        disc_msg, max_tool_calls=5
    )

    console = Console()
    md = Markdown(response["response"])
    console.print(md)

    print(f"Raw: {response}")


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

def test_sandbox():
    sandbox = Sandbox()
    # Get the repository files
    github_kb = GithubKnowledgeBase(UUID('00000000-0000-0000-0000-000000000000'), "Cirr0e")
    code_pages = github_kb.get_files("firecrawl-examples")
    
    # Filter for files in the research_trend_ai_agent directory
    agent_files = [
        page for page in code_pages 
        if page.primary_key.startswith("research_trend_ai_agent/") 
        and page.page_type == CodePageType.CODE
    ]
    
    # Create code_files dictionary
    code_files = {
        page.primary_key.split("/")[-1]: page.content 
        for page in agent_files
    }
    
    print(code_files)
    
    print(sandbox.run_code_e2b(
        code_files, "python research_agent.py --topic 'Generative Agents in 2025'", "pip install -r requirements.txt", timeout=300
    ))

def get_example_contents_llm_readable(repo: str):
    search_tools = SearchTools(requestor_id=FIRECRAWL_ORG_ID)

    # Get list of example directories by fetching contents and filtering for directories
    dirs: List[CodePage] = []
    search_tools.github.fetch_contents(repo, dirs, include_dirs=True)
    example_dirs = [
        item.primary_key for item in dirs
        if item.page_type == CodePageType.DIRECTORY
    ]
    logging.info(f"Found {len(example_dirs)} example directories")

    for example_dir in example_dirs:
        # For each example directory, fetch all its contents
        codefiles: List[CodePage] = []
        search_tools.github.fetch_contents(repo, codefiles, example_dir)
        
        # Create the formatted string for this example
        codefile_str = "\n".join([
            f"<fpath_{codefile.primary_key}>\n{codefile.content}\n</fpath_{codefile.primary_key}>" 
            for codefile in codefiles
        ])

        # Write to a file named after the example. Create directory if it doesn't exist
        logging.info(f"Writing to file: {example_dir}")
        os.makedirs(os.path.dirname(f"examples/{example_dir}"), exist_ok=True)
        output_file = f"examples/{example_dir}.txt"
        with open(output_file, "w") as f:
            f.write(codefile_str)

async def test_webhook():
    # Read the webhook payload from file
    with open("test_webhook.txt", "r") as f:
        payload = f.read()
        if payload.startswith("b'"):
            payload = payload[2:-1]  # Remove b' from start and ' from end

    # Create mock request with proper headers and body
    headers = {
        "host": "localhost:8000",
        "content-type": "application/json",
        "user-agent": "GitHub-Hookshot/123abc",
        "x-github-delivery": "123abc",
        "x-github-event": "pull_request_review_comment",
    }

    # Create a mock request with the payload
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/pr_changes",
        "headers": [(k.encode(), v.encode()) for k, v in headers.items()]
    }
    
    request = Request(scope=scope)
    # Set the request body
    request._body = payload.encode()

    # Import and call the webhook handler
    from main import handle_pr_changes_webhook
    response = await handle_pr_changes_webhook(request)
    print(f"Webhook response: {response}")

if __name__ == "__main__":
    asyncio.run(test_webhook())