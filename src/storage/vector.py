from pymilvus import DataType, CollectionSchema, FieldSchema
from pymilvus import MilvusClient
from pymilvus.milvus_client.index import IndexParams
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from logger import logger
from typing import List, Any, Dict
from uuid import UUID
from dotenv import load_dotenv
import os

from src.model.runbook import Runbook
from src.model.issue import Issue
from src.storage.supa import SupaClient

# Embedding models
NVIDIA_EMBED = "nvidia/NV-Embed-v2"
OPENAI_EMBED = "text-embedding-3-small"
SUPPORTED_MODELS = [NVIDIA_EMBED, OPENAI_EMBED]
DIMENSION = 1536

RUNBOOK = "runbook"
ISSUE = "issue"

load_dotenv()


class EmbeddingModel:
    """
    Wrapper around embedding model so we can switch between diff ones
    easily
    """

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.client = self.get_client(model_name)

    def get_client(self, name: str) -> Any:
        """
        Get the client to generate embeddings over
        """
        if name.lower() == OPENAI_EMBED:
            return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        elif name.lower() == NVIDIA_EMBED:
            return SentenceTransformer(name, trust_remote_code=True)
        else:
            raise f"embedding model not supported. Choose one of {','.join(SUPPORTED_MODELS)}"

    def encode(self, text: str) -> List[List[float]]:
        """
        Encode the provided string
        """
        if self.model_name.lower() == OPENAI_EMBED:
            response = self.client.embeddings.create(
                model=self.model_name,
                input="The food was delicious and the waiter...",
                encoding_format="float",
            )
            return response.data[0].embedding
        elif self.model_name.lower() == NVIDIA_EMBED:
            return self.client.encode([text])[0]
        else:
            raise f"embedding model not supported. Choose one of {','.join(SUPPORTED_MODELS)}"


# VectorDB class wrapping Milvus client and an embedding model
class VectorDB:
    """
    Wrapper around vector db interactions
    """

    def __init__(
        self, user_id: UUID, embedding_model_name: str = OPENAI_EMBED, dimension: int = DIMENSION
    ):
        self.client = MilvusClient(
            uri=os.environ.get("MILVUS_URL"),
            token=os.environ.get("MILVUS_TOKEN"),
            user=os.environ.get("MILVUS_USERNAME"),
        )

        self.embedding_model_name = embedding_model_name
        self.model = EmbeddingModel(embedding_model_name)
        self.dimension = dimension

        self.supa_client = SupaClient(
            user_id,
        )

        self.is_debug_mode = os.environ.get("DEBUG_MODE").lower() == "true"

        self.create_runbook_collection()
        self.create_issue_collection()

    def create_runbook_collection(self):
        """
        Create a runbook collection if doesn't exist, and load it into memory. If exists in db
        already, then we just load into memory
        """
        fields = [
            FieldSchema(
                name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36
            ),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(
                name="description", dtype=DataType.VARCHAR, max_length=65535
            ),  # Adjust max_length as needed
            FieldSchema(
                name="steps",
                dtype=DataType.ARRAY,
                max_capacity=36,
                element_type=DataType.VARCHAR,
                max_length=65535,
            ),
        ]
        schema = CollectionSchema(fields=fields, description="Runbook collection")

        if not self.client.has_collection(RUNBOOK):
            self.client.create_collection(RUNBOOK, schema=schema)
            self.client.create_index(RUNBOOK, IndexParams("vector"))

        self.client.load_collection(RUNBOOK)

    def create_issue_collection(self):
        """
        Create an issue collection if doesn't exist, and load it into memory. If exists in db
        already, then we just load into memory
        """
        fields = [
            FieldSchema(name="primary_key", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="comments", dtype=DataType.JSON),
        ]
        schema = CollectionSchema(fields=fields, description="Issue collection")

        if not self.client.has_collection(ISSUE):
            self.client.create_collection(ISSUE, schema=schema)
            self.client.create_index(ISSUE, IndexParams("vector"))

        self.client.load_collection(ISSUE)

    def vanilla_embed(self, text: str) -> List[float]:
        """
        Embed a string using the embedding model.
        """
        return self.model.encode(text)

    def embed_runbook(self, runbook: Runbook) -> List[float]:
        """
        Embed a runbook description and return it.

        Will be an array of size self.dimension
        """
        # Embed the runbook description using SentenceTransformer
        if self.is_debug_mode:
            return [0.0] * self.dimension

        return self.model.encode(runbook.description)
    
    def issue_to_embeddable_string(self, issue: Issue) -> str:
        """
        Convert an issue to a string that can be embedded
        """
        return issue.description + " " + " ".join(issue.comments.values())

    def embed_issue(self, issue: Issue) -> List[float]:
        """
        Embed an issue description and return it.
        """
        if self.is_debug_mode:
            return [0.0] * self.dimension

        return self.model.encode(self.issue_to_embeddable_string(issue))

    def add_runbook(self, runbook: Runbook):
        """
        Add a new runbook to the vector db
        """
        prev_data = self.client.get(RUNBOOK, runbook.rid)
        if len(prev_data) > 0:
            return  # Runbook already exists, just continue.

        # Embed the description
        vector = self.embed_runbook(runbook)

        # get step ids for db insert
        step_ids = [str(step.sid) for step in runbook.steps]

        # Insert the runbook data into Milvus
        entity = [
            {
                "id": str(runbook.rid),
                "vector": vector,
                "description": runbook.description,
                "steps": step_ids,
            }
        ]

        self.client.insert(RUNBOOK, data=entity)

        # TODO Add steps to step unstructured collection
        self.supa_client.add_steps_for_runbook(runbook)

        print("Successfully added new runbook")

    def add_issue(self, issue: Issue):
        """
        Add a new issue to the vector db.
        """

        # Check if issue already exists
        prev_data = self.client.get(ISSUE, issue.primary_key)
        if len(prev_data) > 0:
            # compare content, if there's even a slight difference, we should update the issue vector.
            prev_data_issue = Issue(**prev_data[0])
            if self.issue_to_embeddable_string(prev_data_issue) == self.issue_to_embeddable_string(issue):
                return  # Issue content is the same as existing issue, just continue.

        vector = self.embed_issue(issue)
        entity = [
            {
                "primary_key": str(issue.primary_key),
                "vector": vector,
                "description": issue.description,
                "comments": issue.comments,
            }
        ]

        self.client.upsert(ISSUE, data=entity)

    def get_all_issues(self) -> List[Issue]:
        """
        Get all issues from the vector db
        """
        issues = self.client.get(ISSUE)
        return [Issue(**issue) for issue in issues]

    def get_top_k_runbooks(self, k: int, query_vector: List[float]) -> Dict[str, Any]:
        """
        Gets top k runbooks.
        """
        top_k_runbooks = {}
        top_k_runbooks[RUNBOOK] = []

        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = self.client.search(
            collection_name=RUNBOOK,
            data=[query_vector],
            anns_field="vector",
            search_params=search_params,
            limit=k,
            output_fields=["vector", "description", "steps"],
        )

        # Format and return the results
        for result in results[0]:
            runbook_id = result["id"]
            vector = result["entity"]["vector"]
            description = result["entity"]["description"]
            step_ids = list(result["entity"]["steps"])
            score = result["distance"]

            # TODO Fetch all step objects given the step ids
            steps = self.supa_client.get_steps_for_runbook(step_ids)

            rb = Runbook(
                rid=runbook_id, description=description, steps=steps, vector=vector
            )

            top_k_runbooks[RUNBOOK].append(
                {"similarity": score, "metadata": rb.model_dump_json()}
            )

        return top_k_runbooks

    def get_top_k_issues(self, k: int, query_vector: List[float]) -> Dict[str, Any]:
        """
        Get top k issues
        """
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = self.client.search(
            collection_name=ISSUE,
            data=[query_vector],
            anns_field="vector",
            search_params=search_params,
            limit=k,
            output_fields=["vector", "description", "comments"],
        )
        
        issues = {}
        for result in results[0]:
            issue_id = result["id"]
            distance = result["distance"]
            problem_description = result["entity"]["description"]
            comments = result["entity"]["comments"]
            vector = result["entity"]["vector"]

            issue = Issue(primary_key=issue_id, description=problem_description, comments=comments, vector=vector)

            issues[issue_id] = {"similarity": distance, "metadata": issue.model_dump_json()}

        return issues
