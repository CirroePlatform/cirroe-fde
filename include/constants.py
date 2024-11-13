from uuid import UUID

# Supabase constants
ORG_NAME = "org_name"

# test constants
MEM0AI_ORG_ID = UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1")
MEM0AI_ORG_NAME = "mem0ai"
MEM0AI_REPO_NAME = "mem0"
MEM0AI_REPO_URL = f"https://github.com/{MEM0AI_ORG_NAME}/{MEM0AI_REPO_NAME}"
MEM0AI_DOCU_URL = "https://docs.mem0.ai/sitemap.xml"

CACHE_DIR = "include/cache"

# Evaluation constants
DEFAULT_TEST_TRAIN_RATIO = 0.2
EVAL_OUTPUT_FILE = "include/eval_output.csv"


# Github constants
CLOSED = "closed"

# Prompt constants
EVAL_AGENT_RESPONSE_PROMPT = "include/prompts/eval_agent_response.txt"
DEBUG_ISSUE_FILE = "include/prompts/debug_issue_tools.txt"
DEBUG_ISSUE_FINAL_PROMPT = "include/prompts/debug_issue_final.txt"
COALESCE_ISSUE_PROMPT = "include/prompts/coalesce_issue.txt"
COALESCE_DOCU_PROMPT = "include/prompts/coalesce_docu.txt"
EVAL_ISSUE_PREPROCESS_PROMPT = "include/prompts/eval_issue_preprocess.txt"

# Model constants
MODEL_LIGHT = "claude-3-5-haiku-latest"
MODEL_HEAVY = "claude-3-5-sonnet-latest"

# Tool constants
DEBUG_TOOLS = [
    {
        "name": "execute_codebase_search",
        "description": "A function to search the teams codebase for relevant code snippets. This will return the top k chunks of code from the teams various codebases relevant to the provided search query.",
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
