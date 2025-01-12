from fastapi import FastAPI, Request, HTTPException
from scripts.firecrawl_demo import get_handler
from scripts.firecrawl_demo import main
from pydantic import BaseModel
import logging
import hashlib
import uvicorn
import json
import hmac

app = FastAPI()
secret = "example-builder"

ACTIONS = set(["created", "edited"])

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

    try:
        # Decode bytes to string and parse JSON
        body_str = request_body.decode('utf-8')
        payload = json.loads(body_str)

        if payload['action'] in ACTIONS and "pull_request" in payload:
            # logging.info(f"Comment on line {line_number} in file {file_path}: {comment_body}. Line diff: {line_diff}")

            # Add logic to handle comments on specific spots
            handler = get_handler()
            response = handler.handle_pr_feedback(payload)
            

        return {"status": "success"}
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse webhook payload: {e}")
        logging.error(f"Raw payload: {request_body}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logging.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # main("create")
    uvicorn.run(app, host="0.0.0.0", port=8000)