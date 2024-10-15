import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests
from uuid import uuid4

from src.model.issue import OpenIssueRequest, Issue

# FastAPI endpoint URL
API_ENDPOINT = "http://your-fastapi-server.com/issue"
SLACK_BOT_TOKEN="SLACK_BOT_TOKEN"

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# class Integration:
#     def __init__(self) -> None:
#         pass

@app.message()
def handle_message(self, message: str, say):
    # Extract relevant information from the Slack message
    requestor = message['user']
    problem_description = message['text']
    
    # Create an Issue object
    issue = Issue(
        tid=str(uuid4()),
        problem_description=problem_description,
        comments=[]  # Initially empty, as this is a new issue
    )
    
    # Create an OpenIssueRequest object
    open_issue_request = OpenIssueRequest(
        requestor=requestor,
        issue=issue
    )
    
    # Send a POST request to the FastAPI endpoint
    response = requests.post(API_ENDPOINT, json=open_issue_request.dict())
    
    if response.status_code == 200:
        # If the request was successful, send a confirmation message
        say(f"Issue created successfully. Issue ID: {issue.tid}")
    else:
        # If there was an error, inform the user
        say("Sorry, there was an error creating the issue. Please try again later.")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()