from typeguard import typechecked
from uuid import UUID
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions
from typing import List, Optional

from src.model.runbook import Runbook, Step


@typechecked
class SupaClient:
    """
    Supabase db client
    """

    def __init__(self, user_id: UUID) -> None:
        load_dotenv()

        self.user_id = user_id
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_API_KEY")
        self.supabase: Client = None

        try:
            self.supabase = create_client(
                url,
                key,
                options=ClientOptions(
                    postgrest_client_timeout=10,
                    storage_client_timeout=10,
                    schema="public",
                ),
            )
        except Exception as e:
            raise ConnectionError(f"Error: Couldn't connect to supabase db. {e}")

        self.steps = self.supabase.table("steps")

    def retrieve_step(self, sid: UUID) -> Optional[Step]:
        """
        Retrieves a step object from Supabase given the sid and bundles it into a Python Step object.

        Args:
            sid (UUID): The UUID of the step to retrieve.

        Returns:
            Optional[Step]: The Step object if found, otherwise None.
        """
        # Query Supabase to retrieve the record by sid
        response = self.steps.select("*").eq("sid", str(sid)).single().execute()

        # Check if the query was successful and data is returned
        if response.get("status_code") == 200 and response.get("data"):
            data = response["data"]

            # Deserialize the allowed_cmds and alt_conditions fields
            allowed_cmds = json.loads(data["allowed_cmds"])

            # Bundle the data into a Step object
            step = Step(
                sid=UUID(data["sid"]),
                description=data["description"],
                allowed_cmds=allowed_cmds,
                next=UUID(data["next"]),
            )

            return step
        else:
            # No data found or some error occurred
            return None

    def add_steps_for_runbook(self, runbook: Runbook):
        """
        Given a runbook, adds all of its steps to the supa db 'steps'.
        """
        for step in runbook.steps:
            data = {
                "sid": str(
                    step.sid
                ),  # Assuming sid can be converted to a string if needed
                "description": step.description,
                "allowed_cmds": json.dumps(
                    step.allowed_cmds
                ),  # Supabase accepts JSON strings
                "next": str(step.next),
            }

            self.steps.insert(data).execute()

    def get_steps_for_runbook(self, step_ids: List[str]) -> List[Step]:
        """
        Given a bunch of steps, gets all the associated steps.
        """
        steps = []
        for step in step_ids:
            # ASSUMING THE FIRST STEP IS THE FIRST IN THE LIST
            step = self.retrieve_step(UUID(step))

            steps.append(step)

        return steps
