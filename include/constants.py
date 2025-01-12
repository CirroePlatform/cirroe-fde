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
EXAMPLE_CREATOR_BASE_TOOLS = [
    {
        "name": "execute_search",
        "description": "A function to search the various knowledge bases for the organization of the example creator for relevant information. This will return the top k chunks of data, depending on the knowledge base, that's relevant to the provided search information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A description of the issue from the user which is used to search the codebase for relevant code snippets, This should be created from the issue description, and can be several sentences long",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of chunks to retrieve from the codebase",
                },
                "knowledge_base": {
                    "type": "string",
                    "enum": [
                        KnowledgeBaseType.CODEBASE,
                        KnowledgeBaseType.ISSUES,
                        KnowledgeBaseType.DOCUMENTATION
                    ],
                    "description": "The knowledge base to use for the search. If the knowledgebase is the web, the results will be from the web, if the search is for code, the results will be from code snippets in the codebase, if the search is for issues, the results will be from the previously solved issues, and if the search is for documentation, the results will be from the org's documentation.",
                },
                "traceback": {
                    "type": "string",
                    "description": "A traceback from the user containing error details that can be used to augment the search for relevant code snippets",
                },
                "user_provided_code": {
                    "type": "string",
                    "description": "A code snippet from the user that is relevant to the issue",
                },
                "user_setup_details": {
                    "type": "string",
                    "description": "A description of the user's setup details, including environment variables, OS, pacakge versions, etc.",
                },
            },
            "required": ["query", "limit", "knowledge_base"],
        },
    }
]

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
                    "description": "The query string",
                    "required": "true"
                },
                "useAutoprompt": {
                    "type": "boolean",
                    "description": "Autoprompt converts your query to an Exa query. Default false. Neural and auto search only."
                },
                "type": {
                    "type": "string",
                    "enum": ["keyword", "neural", "auto"],
                    "description": "The type of search. Default auto, which automatically decides between keyword and neural."
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
                        "financial report"
                    ],
                    "description": "A data category to focus on."
                },
                "numResults": {
                    "type": "integer",
                    "description": "Number of search results to return. Default and Max is 10."
                },
                "includeDomains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of domains to include in the search. If specified, results will only come from these domains."
                },
                "excludeDomains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of domains to exclude in the search. If specified, results will not include any from these domains."
                },
                "startCrawlDate": {
                    "type": "string",
                    "description": "Crawl date refers to the date that Exa discovered a link. Results will include links that were crawled after this date. Must be specified in ISO 8601 format."
                },
                "endCrawlDate": {
                    "type": "string",
                    "description": "Crawl date refers to the date that Exa discovered a link. Results will include links that were crawled before this date. Must be specified in ISO 8601 format."
                },
                "startPublishedDate": {
                    "type": "string",
                    "description": "Only links with a published date after this will be returned. Must be specified in ISO 8601 format."
                },
                "endPublishedDate": {
                    "type": "string",
                    "description": "Only links with a published date before this will be returned. Must be specified in ISO 8601 format."
                },
                "includeText": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of strings that must be present in webpage text of results. Currently, only 1 string is supported, of up to 5 words."
                },
                "excludeText": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of strings that must not be present in webpage text of results. Currently, only 1 string is supported, of up to 5 words."
                },
                "contents": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "object",
                            "description": "Parsed contents of the page.",
                            "properties": {}
                        },
                        "highlights": {
                            "type": "object",
                            "description": "Relevant extract(s) from the webpage.",
                            "properties": {}
                        },
                        "summary": {
                            "type": "object",
                            "description": "Summary of the webpage",
                            "properties": {}
                        },
                        "livecrawl": {
                            "type": "string",
                            "enum": ["never", "fallback", "always"],
                            "description": "Options for livecrawling contents. Default is \"never\" for neural/auto search, \"fallback\" for keyword search."
                        },
                        "livecrawlTimeout": {
                            "type": "integer",
                            "description": "The timeout for livecrawling in milliseconds. Max and default is 10000."
                        },
                        "subpages": {
                            "type": "integer",
                            "description": "The number of subpages to crawl."
                        },
                        "subpageTarget": {
                            "type": "string",
                            "description": "The target subpage or subpages. Can be a single string or an array of strings."
                        }
                    }
                }
            }
        }
    }
]

EXAMPLE_CREATOR_CLASSIFIER_TOOLS = EXAMPLE_CREATOR_BASE_TOOLS + [
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
] # + EXAMPLE_CREATOR_SEARCH_WEB_TOOL

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
                    "description": "The command to only execute the code, without building it",
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

EXAMPLE_CREATOR_MODIFICATION_TOOLS = (
    EXAMPLE_CREATOR_CLASSIFIER_TOOLS + GET_LATEST_VERSION_TOOL
)
EXAMPLE_CREATOR_CREATION_TOOLS = (
    EXAMPLE_CREATOR_BASE_TOOLS + GET_LATEST_VERSION_TOOL
)
EXAMPLE_CREATOR_DEBUGGER_TOOLS = EXAMPLE_CREATOR_BASE_TOOLS + EXAMPLE_CREATOR_RUN_CODE_TOOL # + EXAMPLE_CREATOR_SEARCH_WEB_TOOL

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
