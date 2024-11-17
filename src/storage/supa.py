from typeguard import typechecked
from uuid import UUID
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions
from enum import StrEnum
from typing import Optional
import logging

from src.model.code import CodePage
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
        logging.info(f"setting user data result: {response}")

        self.user_data.update(response)

        return response