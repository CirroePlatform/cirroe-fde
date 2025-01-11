from fastapi import FastAPI, Request, HTTPException
from scripts.firecrawl_demo import main
from pydantic import BaseModel
import logging
import hashlib
import uvicorn
import hmac
from scripts.firecrawl_demo import get_handler

app = FastAPI()
secret = "your_github_webhook_secret"
handler = get_handler()

class GitHubWebhookPayload(BaseModel):
    """
    GitHub webhook payload
    """
    action: str
    comment: dict
    pull_request: dict
    repository: dict

def verify_signature(request_body: bytes, signature: str):
    """
    Verify GitHub signature
    """
    mac = hmac.new(secret.encode(), msg=request_body, digestmod=hashlib.sha256)
    expected_signature = f"sha256={mac.hexdigest()}"
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

@app.post("/pr_changes")
async def handle_pr_changes_webhook(request: Request):
    """
    Handle incoming GitHub webhook
    """
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    request_body = await request.body()
    verify_signature(request_body, signature)

    payload = GitHubWebhookPayload.model_validate_json(request_body)

    print(payload)
    if payload.action == "created" and "pull_request" in payload.comment:
        line_number = payload.comment.get("position")
        file_path = payload.comment.get("path")
        comment_body = payload.comment.get("body")
        line_diff = payload.comment.get("diff_hunk")

        logging.info(f"Comment on line {line_number} in file {file_path}: {comment_body}. Line diff: {line_diff}")

        # Add logic to handle comments on specific spots
        handler.handle_pr_feedback(payload)

    return {"status": "success"}

if __name__ == "__main__":
    main("create")  # TODO remove this for the demo
    # uvicorn.run(app, host="0.0.0.0", port=8000)