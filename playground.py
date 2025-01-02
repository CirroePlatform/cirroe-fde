from scripts.solve_oss_ghub_issues import setup_all_kbs_with_repo
from scripts.oss_ghub_issue_analysis import (
    analyze_repos,
    bulk_extract_github_links,
    analyze_github_issues,
)
from src.storage.supa import SupaClient
from test.eval_agent import Orchestrator
from src.core.event.poll import poll_for_issues
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
    CHROMA_ORG_ID
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
        # MEM0AI_ORG_ID: [2079],
        # CHROMA_ORG_ID: [2571],
        # ARROYO_ORG_ID: [3265, 3292],
        QDRANT_ORG_ID: [],
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
Environment:
Windows 11
Python 3.11
CUDA 12.6
CudNN 9.6

from fastembed import TextEmbedding
embedding_model_gpu = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5", providers=["CUDAExecutionProvider"]
)


2024-12-16 23:44:05.981 | ERROR    | fastembed.common.model_management:download_model:264 - Could not download model from HuggingFace: (MaxRetryError("HTTPSConnectionPool(host='huggingface.co', port=443): Max retries exceeded with url: /api/models/qdrant/bge-small-en-v1.5-onnx-q/revision/main (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)')))"), '(Request ID: 34d2d8e5-8653-4d45-8909-fd660ec75fa1)') Falling back to other sources.
2024-12-16 23:44:05.981 | ERROR    | fastembed.common.model_management:download_model:283 - Could not download model from either source

I also cannot seem to be able to get torch on my machine:

pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

Looking in indexes: https://download.pytorch.org/whl/cu124
WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)'))': /whl/cu124/torch/
Could not fetch URL https://download.pytorch.org/whl/cu124/torch/: There was a problem confirming the ssl certificate: HTTPSConnectionPool(host='download.pytorch.org', port=443): Max retries exceeded with url: /whl/cu124/torch/ (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)'))) - skipping
ERROR: Could not find a version that satisfies the requirement torch (from versions: none)
ERROR: No matching distribution found for torch
Yves
OP
 — Yesterday at 7:12 AM
I could download torch using --trusted-host
Is there something similar for fastembed? 
Yves
OP
 — Today at 12:35 AM
I have installed the transformers lib like this:
pip install transformers --use-feature=truststore

Now I get a different error:
Fetching 5 files: 100%|██████████| 5/5 [00:00<?, ?it/s]
...
  [ 0 ; 9 3 m 2 0 2 4 - 1 2 - 1 7   1 6 : 2 0 : 3 7 . 3 9 1 3 2 0 8   [ W : o n n x r u n t i m e : D e f a u l t ,   o n n x r u n t i m e _ p y b i n d _ s t a t e . c c : 9 6 5   o n n x r u n t i m e : : p y t h o n : : C r e a t e E x e c u t i o n P r o v i d e r I n s t a n c e ]   F a i l e d   t o   c r e a t e   C U D A E x e c u t i o n P r o v i d e r .   R e q u i r e   c u D N N   9 . *   a n d   C U D A   1 2 . * ,   a n d   t h e   l a t e s t   M S V C   r u n t i m e .   P l e a s e   i n s t a l l   a l l   d e p e n d e n c i e s   a s   m e n t i o n e d   i n   t h e   G P U   r e q u i r e m e n t s   p a g e   ( h t t p s : / / o n n x r u n t i m e . a i / d o c s / e x e c u t i o n - p r o v i d e r s / C U D A - E x e c u t i o n P r o v i d e r . h t m l # r e q u i r e m e n t s ) ,   m a k e   s u r e   t h e y ' r e   i n   t h e   P A T H ,   a n d   t h a t   y o u r   G P U   i s   s u p p o r t e d .  [ m 
 C:\Users\ksosuzda\PycharmProjects\MiniServer\.venv\Lib\site-packages\fastembed\common\onnx_model.py:89: RuntimeWarning: Attempt to set CUDAExecutionProvider failed. Current providers: ['CPUExecutionProvider'].If you are using CUDA 12.x, install onnxruntime-gpu via ⁠ pip install onnxruntime-gpu --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/ ⁠
  warnings.warn(
Fetching 5 files: 100%|██████████| 5/5 [00:00<?, ?it/s]
The thing is I already have onnxruntime-gpu installed
Mattaiod — Today at 1:05 AM
@Yves  Facing the same issue, could we get an answer please?

Yves — Today at 5:16 AM
I downloaded the model and trying to run it directly using onnx, but still facing issues

import onnxruntime as ort
from transformers import AutoTokenizer, AutoModel
import numpy as np

session = ort.InferenceSession("./model/bm42/model.onnx")

# Print the input names
print("Input names:", [input.name for input in session.get_inputs()])

tokenizer = AutoTokenizer.from_pretrained("./model/bm42")
session = ort.InferenceSession("./model/bm42/model.onnx", providers=['CUDAExecutionProvider'])

documents = [
    "You should stay, study and sprint.",
    "History can only prepare us to be surprised yet again.",
]

inputs = tokenizer(documents, return_tensors="np", padding=True, truncation=True)
onnx_inputs = {'input_ids': inputs['input_ids']}

embeddings = session.run(None, onnx_inputs)

Is this the correct way to run it?
    """
    from rich.console import Console
    from rich.markdown import Markdown

    disc_msg = DiscordMessage(
        content=disc_msg, author="juan", attachments=[]
    )
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

if __name__ == "__main__":
    poll_wrapper()
    # discord_wrapper()
