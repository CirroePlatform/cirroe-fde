from uuid import UUID

# Supabase constants
ORG_NAME = "org_name"

# test constants
MEM0AI_ORG_ID = UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1")
MEM0AI_ORG_NAME = "mem0ai"
MEM0AI_REPO_NAME = "mem0"
MEM0AI_REPO_URL = f"https://github.com/{MEM0AI_ORG_NAME}/{MEM0AI_REPO_NAME}"
MEM0AI_DOCU_URL = "https://docs.mem0.ai/sitemap.xml"

# Evaluation constants
DEFAULT_TEST_TRAIN_RATIO = 0.2

# Github constants
CLOSED = "closed"

# Prompt constants
EVAL_AGENT_RESPONSE_PROMPT = "include/prompts/eval_agent_response.txt"

# Model constants
MODEL_LIGHT = "claude-3-haiku-20240307"
MODEL_HEAVY = "claude-3-5-sonnet-20240620"
