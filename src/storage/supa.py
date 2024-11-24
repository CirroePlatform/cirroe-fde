from typeguard import typechecked
from uuid import UUID
import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions
from enum import StrEnum
import logging

from include.constants import CACHED_USER_DATA_FILE


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

    def get_user_data(self, *columns, debug: bool = False):
        """
        Gets user data based on requested columns

        Args:
            *columns: Column names to retrieve
            debug: Whether to run in debug mode
        """

        def __mock_get_user_data_from_file(self):
            if not os.path.exists(CACHED_USER_DATA_FILE):
                logging.error(
                    f"Cached user data file does not exist at {CACHED_USER_DATA_FILE}, even though debug is true"
                )
                return None

            with open(CACHED_USER_DATA_FILE, "r") as f:
                cached_user_data = json.load(f)
                return cached_user_data[str(self.user_id)]

        if debug:
            response = __mock_get_user_data_from_file(self)
            response = {column: response[column] for column in columns}
        else:
            response = (
                self.supabase.table(Table.USERS)
                .select(*columns)
                .eq(USER_ID, str(self.user_id))
                .execute()
            ).data[0]

        self.user_data.update(response)

        return response

    def set_user_data(self, debug: bool = False, **kwargs):
        """
        Sets user data based on provided kwargs.
        """

        def __mock_set_user_data(self, **kwargs):
            with open(CACHED_USER_DATA_FILE, "r") as f:
                cached_user_data = json.load(f)
                cached_user_data[str(self.user_id)] = kwargs

            with open(CACHED_USER_DATA_FILE, "w") as f:
                json.dump(cached_user_data, f)
                return cached_user_data[str(self.user_id)]

        if debug:
            response = __mock_set_user_data(self, **kwargs)
        else:
            response = (
                self.supabase.table(Table.USERS)
                .update(kwargs)
                .eq(USER_ID, str(self.user_id))
                .execute()
            )
            logging.info(f"setting user data result: {response}")

        self.user_data.update(response)

        return response
