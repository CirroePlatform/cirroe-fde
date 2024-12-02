from fastapi.middleware.cors import CORSMiddleware
from src.core.event.poll import poll_for_issues, bot, disc_token
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

@app.get("/discord_bot")
def discord_bot(background_tasks: BackgroundTasks):
    """
    Spawns a listener for new messages in the discord channel and responses appropriately.
    """
    background_tasks.add_task(run_discord_bot)

    def run_discord_bot():
        # Run the bot
        bot.run(disc_token)