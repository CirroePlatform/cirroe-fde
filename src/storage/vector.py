from pymilvus import DataType, CollectionSchema, FieldSchema, Collection
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Any
from uuid import UUID
from dotenv import load_dotenv
from openai import OpenAI
import os

from src.model.runbook import Runbook

# Embedding models
NVIDIA_EMBED = "nvidia/NV-Embed-v2"
OPENAI_EMBED = "text-embedding-3-small"
SUPPORTED_MODELS = [NVIDIA_EMBED, OPENAI_EMBED]
DIMENSION=1536

RUNBOOK="runbook"

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
                encoding_format="float"
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
        self,
        embedding_model_name: str = OPENAI_EMBED,
        dimension: int = DIMENSION
    ):
        self.collection_name = RUNBOOK
        self.client = MilvusClient(
                    uri=os.environ.get("MILVUS_URL"),
                    token=os.environ.get("MILVUS_TOKEN"),
                    user=os.environ.get("MILVUS_USERNAME"))

        self.embedding_model_name = embedding_model_name
        self.model = EmbeddingModel(embedding_model_name)
        self.dimension = dimension
        self.create_runbook_collection()

    def create_runbook_collection(self):
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=65535),  # Adjust max_length as needed
            FieldSchema(name="first_step", dtype=DataType.VARCHAR, max_length=36),
        ]
        schema = CollectionSchema(fields=fields, description="Runbook collection")

        if not self.client.has_collection(self.collection_name):
            self.client.create_collection(self.collection_name, schema=schema)
            # self.client.create_index(self.collection_name, ) # todo

    def embed_runbook(self, runbook: Runbook) -> List[float]:
        """
        Embed a runbook description and return it.

        Will be an array of size self.dimension
        """
        # Embed the runbook description using SentenceTransformer
        return self.model.encode(runbook.description)

    def add_runbook(self, runbook: Runbook):
        """
        Add a new runbook to the vector db
        """
        prev_data = self.client.get(self.collection_name, runbook.rid)
        if len(prev_data) > 0:
            return # Runbook already exists, just continue.

        # Embed the description
        vector = self.embed_runbook(runbook)

        # Insert the runbook data into Milvus
        entity = [
            {
                "id": str(runbook.rid),
                "vector": vector,
                "description": runbook.description,
                "first_step": str(runbook.first_step_id)
            }
        ]

        self.client.insert(self.collection_name, data=entity)
        print("Successfully added new runbook")

    def get_top_k(self, runbook: Runbook, k: int) -> List[Tuple[UUID, float]]:
        """
        Top k similar runbooks and their distances.
        
        returns a list: [(runbook_id, distance score)]
        """
        # Embed the description for similarity search
        query_vector = self.embed_runbook(runbook.description)

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
            score = result.distance
            top_k_runbooks.append((runbook_id, score))

        return top_k_runbooks
