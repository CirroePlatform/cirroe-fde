from pymilvus import DataType, CollectionSchema, FieldSchema
from pymilvus import MilvusClient
from pymilvus.milvus_client.index import IndexParams
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Any
from uuid import UUID
from dotenv import load_dotenv
from openai import OpenAI
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
        self, embedding_model_name: str = OPENAI_EMBED, dimension: int = DIMENSION
    ):
        self.collection_name = RUNBOOK
        self.client = MilvusClient(
            uri=os.environ.get("MILVUS_URL"),
            token=os.environ.get("MILVUS_TOKEN"),
            user=os.environ.get("MILVUS_USERNAME"),
        )

        self.embedding_model_name = embedding_model_name
        self.model = EmbeddingModel(embedding_model_name)
        self.dimension = dimension

        self.supa_client = SupaClient(
            UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1")
        )  # Hardcoded for now, not actually used
        self.create_runbook_collection()

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

        if not self.client.has_collection(self.collection_name):
            self.client.create_collection(self.collection_name, schema=schema)
            self.client.create_index(self.collection_name, IndexParams("vector"))

        self.client.load_collection(self.collection_name)

    def embed_runbook(self, runbook: Runbook, debug: bool = True) -> List[float]:
        """
        Embed a runbook description and return it.

        Will be an array of size self.dimension
        """
        # Embed the runbook description using SentenceTransformer
        if debug:
            return [0.0] * self.dimension

        return self.model.encode(runbook.description)

    def embed_issue(self, issue: Issue, debug: bool = True) -> List[float]:
        """
        embed an issue and return the resulting vector

        TODO add comments in there as some nice string formatted thing.
        """
        if debug:
            return [0.0] * self.dimension

        return self.model.encode(issue.problem_description)

    def add_runbook(self, runbook: Runbook):
        """
        Add a new runbook to the vector db
        """
        prev_data = self.client.get(self.collection_name, runbook.rid)
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

        self.client.insert(self.collection_name, data=entity)

        # TODO Add steps to step unstructured collection
        self.supa_client.add_steps_for_runbook(runbook)

        print("Successfully added new runbook")

    def get_top_k(
        self, query_vector: List[float], k: int
    ) -> List[Tuple[Runbook, float]]:
        """
        Top k similar runbooks and their distances.

        returns a list: [(runbook_id, distance score)]
        """
        # ensure dimensionality
        if len(query_vector) != self.dimension:
            raise f"Can't compare incorrect dimension vector, expected {self.dimension} got {len(query_vector)}"

        # Perform the search using cosine similarity
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=k,
        )

        # Format and return the results
        top_k_runbooks = []
        for result in results[0]:
            runbook_id = result.id
            vector = result.vector
            description = result.description
            step_ids = result.steps
            score = result.distance

            # TODO Fetch all step objects given the step ids
            steps = self.supa_client.get_steps_for_runbook(step_ids)

            rb = Runbook(
                rid=runbook_id, description=description, steps=steps, vector=vector
            )
            top_k_runbooks.append((rb, score))

        return top_k_runbooks
