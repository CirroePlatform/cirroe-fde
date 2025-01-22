from uuid import UUID
from enum import StrEnum


class KnowledgeBaseType(StrEnum):
    CODEBASE = "codebase"
    ISSUES = "issues"
    DOCUMENTATION = "documentation"
    WEB = "web"


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
LIGHT_DASH_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174009")
MINDEE_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174014")
VIDEO_DB_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174023")
CHROMA_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174027")
FIRECRAWL_ORG_ID = UUID("123e4567-e89b-12d3-a456-426614174028")

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

ACTION_CLASSIFIER = "include/prompts/example_builder/action_classifier.txt"
EXECUTE_CREATION = "include/prompts/example_builder/execute_creation.txt"
EXECUTE_MODIFICATION = "include/prompts/example_builder/execute_modification.txt"

# Model constants
MODEL_LIGHT = "claude-3-5-haiku-latest"
MODEL_HEAVY = "claude-3-5-sonnet-latest"

# Tool constants
# Feel like we should only include this for complete failure cases.
EXAMPLE_CREATOR_SEARCH_WEB_TOOL = [
    {
        "name": "search_web",
        "description": "Search the web with the EXA search engine. Will return a list of links relevant to your query and optionally get their full page contents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A natural language query to search the web with, can be a keyword or a question, or larger set of text/keywords",
                },
                "useAutoprompt": {
                    "type": "boolean",
                    "description": "Autoprompt converts your query to an Exa query. Default false. Neural and auto search only.",
                },
                "type": {
                    "type": "string",
                    "enum": ["keyword", "neural", "auto"],
                    "description": "The type of search. Default auto, which automatically decides between keyword and neural.",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "company",
                        "research paper",
                        "news",
                        "pdf",
                        "github",
                        "tweet",
                        "personal site",
                        "linkedin profile",
                        "financial report",
                    ],
                    "description": "A data category to focus on.",
                },
                "startPublishedDate": {
                    "type": "string",
                    "description": "Only links with a published date after this will be returned. Must be specified in ISO 8601 format.",
                },
                "endPublishedDate": {
                    "type": "string",
                    "description": "Only links with a published date before this will be returned. Must be specified in ISO 8601 format.",
                },
            },
            "required": ["query"],
        },
    }
]
# "cache_control": {"type": "ephemeral"}

DOCUMENTATION_TOOL = [
    {
        "name": "search_documentation",
        "description": "A function to search the documentation for the organization of the example creator for relevant information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A natural language query to search the documentation for relevant information.",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of chunks to retrieve from the documentation.",
                },
            },
            "required": ["query", "limit"],
        },
    }
]

CODE_TOOL = [
    {
        "name": "search_code",
        "description": "A function to search the codebase for the organization of the example creator for relevant information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A natural language query to search the codebase against for relevant code snippets",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of chunks to retrieve from the codebase.",
                },
                "traceback": {
                    "type": "string",
                    "description": "A traceback from the user containing error details that can be used to augment the search for relevant code snippets",
                },
                "setup_details": {
                    "type": "string",
                    "description": "A description of setup details of the example creator that can be used to augment the search for relevant code snippets, including environment variables, OS, package versions, etc.",
                },
            },
            "required": ["query", "limit"],
        },
    }
]

EXAMPLE_CREATOR_BASE_TOOLS = (
    DOCUMENTATION_TOOL + CODE_TOOL + EXAMPLE_CREATOR_SEARCH_WEB_TOOL
)

GET_LATEST_VERSION_TOOL = [
    {
        "name": "get_latest_version",
        "description": "A function to get the latest version of a given pip dependency from PyPI",
        "input_schema": {
            "type": "object",
            "properties": {
                "package_name": {
                    "type": "string",
                    "description": "The name of the pip dependency",
                }
            },
        },
    }
]

EXAMPLE_CREATOR_RUN_CODE_TOOL = [
    {
        "name": "run_code_e2b",
        "description": "A function to run the code in the example with E2B sandbox, and get the stdout and stderr",
        "input_schema": {
            "type": "object",
            "properties": {
                "code_files": {
                    "type": "object",
                    "description": "The code files to run, in the format of a dictionary mapping filenames to code content",
                },
                "execution_command": {
                    "type": "string",
                    "description": "The command to only execute or build the code",
                },
                "build_command": {
                    "type": "string",
                    "description": "The command to build the code, install any dependencies, or set up the environment in any other way",
                },
                "timeout": {
                    "type": "integer",
                    "description": "The timeout for the code execution in seconds. Default is 60 seconds.",
                },
            },
            "required": ["code_files", "execution_command"],
        },
    },
] + GET_LATEST_VERSION_TOOL

EXAMPLE_CREATOR_CLASSIFIER_TOOLS = (
    EXAMPLE_CREATOR_BASE_TOOLS
    + [
        {
            "name": "get_existing_examples",
            "description": "A function to get list of example filenames from the firecrawl/examples directory on GitHub",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "get_example_contents",
            "description": "A function to recursively fetch contents of a repository from GitHub API",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository name to fetch contents from",
                    },
                    "code_pages": {
                        "type": "array",
                        "description": "List to append CodePage objects to",
                    },
                    "path": {
                        "type": "string",
                        "description": "Current path being fetched in the repository",
                    },
                },
                "required": ["repository"],
            },
        },
    ]
    + EXAMPLE_CREATOR_RUN_CODE_TOOL
)

EXAMPLE_CREATOR_MODIFICATION_TOOLS = EXAMPLE_CREATOR_CLASSIFIER_TOOLS
EXAMPLE_CREATOR_CREATION_TOOLS = (
    EXAMPLE_CREATOR_RUN_CODE_TOOL + EXAMPLE_CREATOR_BASE_TOOLS
)
EXAMPLE_CREATOR_DEBUGGER_TOOLS = (
    EXAMPLE_CREATOR_BASE_TOOLS + EXAMPLE_CREATOR_RUN_CODE_TOOL
)
EXAMPLE_CREATOR_PR_TOOLS = EXAMPLE_CREATOR_BASE_TOOLS + EXAMPLE_CREATOR_RUN_CODE_TOOL

# Embedding models
NVIDIA_EMBED = "nvidia/NV-Embed-v2"
OPENAI_EMBED = "text-embedding-3-small"
VOYAGE_CODE_EMBED = "voyage-code-3"
SUPPORTED_MODELS = [NVIDIA_EMBED, OPENAI_EMBED, VOYAGE_CODE_EMBED]
DIMENSION_OPENAI = 1536
DIMENSION_NVIDIA = 4096
DIMENSION_VOYAGE = 2048

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

# Crawl constants
NEWSCHECK_INTERVAL_HOURS = 1
SUBREDDIT_LIST = ["singularity", "aiagents", "LLMDevs", "LLM"]

# keyworks that would find in code
TS_KEYWORDS = [
    "ts",
    "js",
    "async",
    "function",
    "await",
    "promise",
    "import",
    "export",
    "class",
    "interface",
    "type",
    "enum",
    "const",
    "let",
    "var",
    "if",
    "else",
    "switch",
    "case",
    "default",
    "break",
    "continue",
    "return",
    "throw",
    "try",
    "catch",
    "finally",
    "while",
    "for",
    "do",
    "while",
    "of",
    "in",
    "from",
    "as",
    "async",
    "await",
    "yield",
    "async",
    "await",
    "yield",
    "async",
    "await",
    "yield",
]
PYTHON_KEYWORDS = [
    "import",
    "export",
    "class",
    "interface",
    "type",
    "enum",
    "const",
    "let",
    "var",
    "if",
    "elif",
    "else:",
    "default",
    "break",
    "continue",
    "return",
    "throw",
    "try",
    "catch",
    "finally",
    "while",
    "for",
    "do",
    "while",
    "of",
    "in",
    "from",
    "as",
    "async",
    "await",
    "yield",
    "async",
    "await",
    "yield",
    "async",
    "await",
    "yield",
]
