from fastapi.middleware.cors import CORSMiddleware
from src.core.event.poll import poll_for_issues
from src.core.event.poll_discord import dsc_poll_main
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/poll_for_issues/{org_id}/{repo_name}")
def poll_for_issues(org_id: str, repo_name: str, background_tasks: BackgroundTasks):
    """
    Handles the case of a new issue being created. Triggered from a merge api webhook
    """
    background_tasks.add_task(poll_for_issues, org_id, repo_name)

if __name__ == "__main__":
    dsc_poll_main()
