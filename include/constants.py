from uuid import UUID

# Supabase constants
ORG_NAME = "org_name"
REPO_NAME = "repo_name"
CACHE_DIR = "include/cache"
CACHED_USER_DATA_FILE = f"{CACHE_DIR}/cached_user_data.json"

# Org IDs
BASETEN_ORG_ID = UUID("802f083b-5d7e-4418-bebc-6052f5634f8e")
QDRANT_ORG_ID = UUID("a54c3511-0424-4663-8309-1d7ba3953aa6")

UNSLOTH_ORG_ID = UUID("b3848a28-a535-4d5d-b773-34b23e195687")
MEM0AI_ORG_ID = UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1")
UEBERDOSIS_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174000")
MILVUS_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174001")
TRIGGER_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174002")
REFLEX_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174003")

GRAVITL_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174004")
MITO_DS_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174005")
FLOWISE_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174006")
ARROYO_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174007")
PREDIBASE_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174008")

GITFILES_CACHE_DIR = f"{CACHE_DIR}/gitfiles"

# Evaluation constants
DEFAULT_TEST_TRAIN_RATIO = 0.2
EVAL_OUTPUT_FILE = "include/eval_output.csv"

# Github constants
CLOSED = "closed"
INDEX_WITH_GREPTILE = False
GITHUB_API_BASE = "https://api.github.com"

# Prompt constants
EVAL_AGENT_RESPONSE_PROMPT = "include/prompts/eval_agent_response.txt"
DEBUG_ISSUE_FILE = "include/prompts/debug_issue_tools.txt"
DEBUG_ISSUE_FINAL_PROMPT = "include/prompts/debug_issue_final.txt"
COALESCE_ISSUE_PROMPT = "include/prompts/coalesce_issue.txt"
EVAL_ISSUE_PREPROCESS_PROMPT = "include/prompts/eval_issue_preprocess.txt"
REQUIRES_DEV_TEAM_PROMPT = "include/prompts/requires_dev_team_prompt.txt"
DEBUG_DISCORD_FILE = "include/prompts/debug_discord.txt"

# Model constants
MODEL_LIGHT = "claude-3-5-haiku-latest"
MODEL_HEAVY = "claude-3-5-sonnet-latest"

# Tool constants
DEBUG_TOOLS = [
    {
        "name": "execute_codebase_search",
        "description": "A function to search the teams codebase for relevant code snippets. This will return the top k chunks of code from the teams' code base that's relevant to the provided search query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A description of the issue from the user which is used to search the codebase for relevant code snippets",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of chunks to retrieve from the codebase",
                },
                "traceback": {
                    "type": "string",
                    "description": "A traceback from the user containing error details that can be used to augment the search for relevant code snippets",
                },
            },
            "required": ["query", "limit"],
        },
    },
    {
        "name": "execute_issue_search",
        "description": "This is a knowledge base of previous issues from users, the response here would contain a list of issues with comments and descriptions from users and engineers, and the whether the issue has been resolved.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A natural language query about previous issues",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of issues to retrieve",
                },
            },
            "required": ["query", "limit"],
        },
    },
    {
        "name": "execute_documentation_search",
        "description": "A function to search the teams documentation for relevant information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A natural language query about the documentation",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of documents to retrieve",
                },
            },
            "required": ["query", "limit"],
        },
    },
]

# Embedding models
NVIDIA_EMBED = "nvidia/NV-Embed-v2"
OPENAI_EMBED = "text-embedding-3-small"
SUPPORTED_MODELS = [NVIDIA_EMBED, OPENAI_EMBED]
DIMENSION_OPENAI = 1536
DIMENSION_NVIDIA = 4096

# Vector DB constants
DOCUMENTATION = "documentation"
RUNBOOK = "runbook"
ISSUE = "issue"
CODE = "code"

# Poll constants
POLL_INTERVAL = 10
BUG_LABELS = ["bug", "question"]
ABHIGYA_USERNAME = "AbhigyaWangoo"
CIRROE_USERNAME = "Cirr0e"

# Finetune constants
DEFAULT_NEEDS_DEV_TEAM_OUTPUT_PATH = "include/needs_dev_team_output.jsonl"

# Discord constants
CHANNEL = "cirroe-support"
