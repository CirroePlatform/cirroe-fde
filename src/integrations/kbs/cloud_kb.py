import subprocess
import json
import os
from typing import Any, Dict, List
from src.storage.supa import SupaClient
from logger import logger
from src.integrations.kbs.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse


class CloudIntegration(BaseKnowledgeBase):
    def __init__(self, org_id: str):
        """
        Initialize cloud integration with organization ID to fetch credentials.

        Args:
            org_id (str): Organization ID to lookup cloud credentials
        """
        super().__init__(org_id)
        self.supa_client = SupaClient()
        self.credentials = self._get_credentials()

    def _get_credentials(self) -> Dict[str, Dict[str, str]]:
        """
        Retrieve cloud credentials from Supabase for the organization.

        Returns:
            Dict containing credentials for each cloud provider
        """
        try:
            result = (
                self.supa_client.table("cloud_credentials")
                .select("*")
                .eq("org_id", self.org_id)
                .execute()
            )

            if not result.data:
                logger.warning(f"No cloud credentials found for org_id: {self.org_id}")
                return {}

            credentials = {}
            for cred in result.data:
                provider = cred["provider"]
                credentials[provider] = json.loads(cred["credentials"])

            return credentials

        except Exception as e:
            logger.error(f"Error retrieving cloud credentials: {str(e)}")
            return {}

    def _set_temp_credentials(self, provider: str) -> None:
        """
        Temporarily set cloud provider credentials as environment variables.

        Args:
            provider (str): Cloud provider to set credentials for
        """
        if provider not in self.credentials:
            raise ValueError(f"No credentials found for {provider}")

        if provider == "aws":
            os.environ["AWS_ACCESS_KEY_ID"] = self.credentials["aws"]["access_key_id"]
            os.environ["AWS_SECRET_ACCESS_KEY"] = self.credentials["aws"][
                "secret_access_key"
            ]
            if "session_token" in self.credentials["aws"]:
                os.environ["AWS_SESSION_TOKEN"] = self.credentials["aws"][
                    "session_token"
                ]

        elif provider == "azure":
            os.environ["AZURE_CLIENT_ID"] = self.credentials["azure"]["client_id"]
            os.environ["AZURE_CLIENT_SECRET"] = self.credentials["azure"][
                "client_secret"
            ]
            os.environ["AZURE_TENANT_ID"] = self.credentials["azure"]["tenant_id"]

        elif provider == "gcp":
            # For GCP, write service account JSON to temporary file
            import tempfile

            fd, path = tempfile.mkstemp()
            with os.fdopen(fd, "w") as tmp:
                json.dump(self.credentials["gcp"], tmp)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path

    def _clear_temp_credentials(self, provider: str) -> None:
        """
        Clear temporary cloud provider credentials from environment.

        Args:
            provider (str): Cloud provider to clear credentials for
        """
        if provider == "aws":
            os.environ.pop("AWS_ACCESS_KEY_ID", None)
            os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
            os.environ.pop("AWS_SESSION_TOKEN", None)
        elif provider == "azure":
            os.environ.pop("AZURE_CLIENT_ID", None)
            os.environ.pop("AZURE_CLIENT_SECRET", None)
            os.environ.pop("AZURE_TENANT_ID", None)
        elif provider == "gcp":
            cred_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_file and os.path.exists(cred_file):
                os.remove(cred_file)
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

    async def index(self, data: Any) -> bool:
        """
        Not implemented for cloud integration.
        """
        return False

    def query(self, query: str, limit: int = 5) -> List[KnowledgeBaseResponse]:
        """
        Not implemented for cloud integration.
        """
        return []

    def execute_command(self, provider: str, command: str) -> Dict[str, Any]:
        """
        Execute a read-only command for the specified cloud provider.

        Args:
            provider (str): Cloud provider (aws, azure, or gcp)
            command (str): The command to execute

        Returns:
            Dict[str, Any]: The output of the command execution
        """
        provider = provider.lower()
        if provider not in ["aws", "azure", "gcp"]:
            raise ValueError(
                "Unsupported cloud provider. Choose from 'aws', 'azure', or 'gcp'."
            )

        try:
            self._set_temp_credentials(provider)

            if provider == "aws":
                result = subprocess.run(
                    ["aws"] + command.split(),
                    capture_output=True,
                    text=True,
                    check=True,
                )
            elif provider == "azure":
                result = subprocess.run(
                    ["az"] + command.split(), capture_output=True, text=True, check=True
                )
            elif provider == "gcp":
                result = subprocess.run(
                    ["gcloud"] + command.split(),
                    capture_output=True,
                    text=True,
                    check=True,
                )

            return {"success": True, "output": result.stdout, "error": result.stderr}

        except subprocess.CalledProcessError as e:
            return {"success": False, "output": e.stdout, "error": e.stderr}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
        finally:
            self._clear_temp_credentials(provider)
