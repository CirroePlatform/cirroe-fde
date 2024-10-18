import merge
from merge.client import Merge
from dotenv import load_dotenv
import os

load_dotenv()

client = Merge(api_key=os.environ.get("MERGE_ACCESS_KEY"), account_token=os.environ.get("JIRA_TEST_TOKEN"))

print(client.ticketing.tickets.list())