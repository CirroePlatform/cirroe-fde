from uuid import UUID

# Supabase constants
ORG_NAME = "org_name"

# Unsloth
UNSLOTH_ORG_ID = UUID("b3848a28-a535-4d5d-b773-34b23e195687")
UNSLOTH_REPO_NAME = "unsloth"
UNSLOTH_DOCU_URL = "https://docs.unsloth.ai/sitemap.xml"
UNSLOTH_ORG_NAME = "unslothai"
UNSLOTH_REPO_URL = f"https://github.com/{UNSLOTH_ORG_NAME}/{UNSLOTH_REPO_NAME}"

# Mem0
MEM0AI_ORG_ID = UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1")
MEM0AI_ORG_NAME = "mem0ai"
MEM0AI_REPO_NAME = "mem0"
MEM0AI_REPO_URL = f"https://github.com/{MEM0AI_ORG_NAME}/{MEM0AI_REPO_NAME}"
MEM0AI_DOCU_URL = "https://docs.mem0.ai/sitemap.xml"

# Baseten
BASETEN_ORG_ID = UUID("802f083b-5d7e-4418-bebc-6052f5634f8e")
BASETEN_ORG_NAME = "basetenlabs"
BASETEN_REPO_NAME = "truss"
BASETEN_REPO_URL = f"https://github.com/{BASETEN_ORG_NAME}/{BASETEN_REPO_NAME}"
BASETEN_DOCU_URL = "https://docs.baseten.co/sitemap.xml"

# Qdrant
QDRANT_ORG_ID = UUID("a54c3511-0424-4663-8309-1d7ba3953aa6")
QDRANT_ORG_NAME = "qdrant"
QDRANT_REPO_NAME = "qdrant"
QDRANT_REPO_URL = f"https://github.com/{QDRANT_ORG_NAME}/{QDRANT_REPO_NAME}"
QDRANT_DOCU_URL = "https://qdrant.tech/sitemap.xml"

CACHE_DIR = "include/cache"
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

# Model constants
MODEL_LIGHT = "claude-3-5-haiku-latest"
MODEL_HEAVY = "claude-3-5-sonnet-latest"

# Tool constants
DEBUG_TOOLS = [
    # {
    #     "name": "execute_codebase_search",
    #     "description": "A function to search the teams codebase for relevant code snippets. This will return the top k chunks of code from the teams various codebases relevant to the provided search query.",
    #     "input_schema": {
    #         "type": "object",
    #         "properties": {
    #             "query": {
    #                 "type": "string",
    #                 "description": "A description of the issue from the user which is used to search the codebase for relevant code snippets",
    #             },
    #             "limit": {
    #                 "type": "integer",
    #                 "description": "The number of chunks to retrieve from the codebase",
    #             },
    #         },
    #         "required": ["query", "limit"],
    #     },
    # },
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
