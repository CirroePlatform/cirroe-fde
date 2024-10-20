from typeguard import typechecked
from uuid import UUID
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions
from typing import List, Optional
from enum import StrEnum

from src.model.runbook import Runbook, Step


class Table(StrEnum):
    USERS = "UserMetadata"
    CHAT_SESSIONS = "ChatSessions"
    CHATS = "Chats"


USER_ID = "user_id"
ACCOUNT_TOKEN = "account_token"


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
        self.user_data = {}

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
        Retrieves a step object from Supabase given the sid and
        bundles it into a Python Step object.

        Args:
            sid (UUID): The UUID of the step to retrieve.

        Returns:
            Optional[Step]: The Step object if found, otherwise None.
        """
        # Query Supabase to retrieve the record by sid
        response = self.steps.select("*").eq("sid", str(sid)).single().execute()

        # Check if the query was successful and data is returned
        if len(response.data) > 0:
            data = response.data

            # Deserialize the allowed_cmds and alt_conditions fields
            allowed_cmds = json.loads(data["allowed_cmds"])

            # Bundle the data into a Step object
            step = Step(
                sid=UUID(data["sid"]),
                description=data["description"],
                allowed_cmds=allowed_cmds,
            )

            if data["next"] is not None:
                step.next = UUID(data["next"])

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
            }

            if step.next is not None:
                data["next"] = str(step.next)

            self.steps.upsert(data).execute()

    def get_steps_for_runbook(self, step_ids: List[str]) -> List[Step]:
        """
        Given a bunch of steps, gets all the associated steps.
        """
        steps = []
        for step in step_ids:
            # ASSUMING THE FIRST STEP IS THE FIRST IN THE LIST
            step_obj = self.retrieve_step(UUID(step))

            steps.append(step_obj)

        return steps

    def get_user_data(self, *columns):
        """
        Gets user data based on requested columns
        """
        response = (
            self.supabase.table(Table.USERS)
            .select(*columns)
            .eq(USER_ID, str(self.user_id))
            .execute()
        ).data[0]

        self.user_data.update(response)

        return response

    def set_user_data(self, **kwargs):
        """
        Sets user data based on provided kwargs.
        """
        response = (
            self.supabase.table(Table.USERS)
            .update(kwargs)
            .eq(USER_ID, str(self.user_id))
            .execute()
        )
        print(f"setting user data result: {response}")

        self.user_data.update(response)

        return response
