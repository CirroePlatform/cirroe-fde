from include.constants import DOCUMENTATION, ISSUE, RUNBOOK, CODE, NVIDIA_EMBED, OPENAI_EMBED, DIMENSION_OPENAI, DIMENSION_NVIDIA, SUPPORTED_MODELS
from pymilvus import DataType, CollectionSchema, FieldSchema
from src.model.documentation import DocumentationPage
from sentence_transformers import SentenceTransformer
from pymilvus.milvus_client.index import IndexParams
from typing import List, Any, Dict, Union
from src.storage.supa import SupaClient
from src.model.code import CodePage
from pymilvus import MilvusClient
from typeguard import typechecked
from src.model.issue import Issue
from dotenv import load_dotenv
from openai import OpenAI
from uuid import UUID
import os


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
        if name.lower() == OPENAI_EMBED.lower():
            return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        elif name.lower() == NVIDIA_EMBED.lower():
            return SentenceTransformer(name, trust_remote_code=True)
        else:
            raise ValueError(f"embedding model not supported. Choose one of {','.join(SUPPORTED_MODELS)}")

    def encode(self, text: str) -> List[List[float]]:
        """
        Encode the provided string
        """
        if self.model_name.lower() == OPENAI_EMBED.lower():
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text,
                encoding_format="float",
            )
            return response.data[0].embedding
        elif self.model_name.lower() == NVIDIA_EMBED.lower():
            return self.client.encode([text])[0]
        else:
            raise ValueError(f"embedding model not supported. Choose one of {','.join(SUPPORTED_MODELS)}")


# VectorDB class wrapping Milvus client and an embedding model
class VectorDB:
    """
    Wrapper around vector db interactions
    """

    def __init__(
        self,
        user_id: UUID,
        embedding_model_name: str = OPENAI_EMBED,
        dimension: int = DIMENSION_OPENAI,
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
        self.user_id = user_id

        self.create_issue_collection()
        self.create_documentation_collection()
        self.create_code_collection()
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
            FieldSchema(
                name="primary_key",
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=36,
            ),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="comments", dtype=DataType.JSON),
            FieldSchema(name="org_id", dtype=DataType.VARCHAR, max_length=36),
        ]
        schema = CollectionSchema(fields=fields, description="Issue collection")

        if not self.client.has_collection(ISSUE):
            self.client.create_collection(ISSUE, schema=schema)
            self.client.create_index(ISSUE, IndexParams("vector"))

        self.client.load_collection(ISSUE)

    def create_documentation_collection(self):
        """
        Create a documentation collection if doesn't exist, and load it into memory. If exists in db
        already, then we just load into memory
        """
        fields = [
            FieldSchema(
                name="primary_key",
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=64,  # 16 bytes -> 32 hex characters for SHA3-256 hash
            ),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="url", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="org_id", dtype=DataType.VARCHAR, max_length=36),
        ]
        schema = CollectionSchema(fields=fields, description="Documentation collection")

        if not self.client.has_collection(DOCUMENTATION):
            self.client.create_collection(DOCUMENTATION, schema=schema)
            self.client.create_index(DOCUMENTATION, IndexParams("vector"))

        self.client.load_collection(DOCUMENTATION)

    def create_code_collection(self):
        """
        Create a code collection if doesn't exist, and load it into memory. If exists in db
        already, then we just load into memory
        """
        fields = [
            FieldSchema(
                name="primary_key",
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=36,
            ),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="org_id", dtype=DataType.VARCHAR, max_length=36),
            FieldSchema(name="page_type", dtype=DataType.VARCHAR, max_length=32),
        ]
        schema = CollectionSchema(fields=fields, description="Code collection")

        if not self.client.has_collection(CODE):
            self.client.create_collection(CODE, schema=schema)
            self.client.create_index(CODE, IndexParams("vector"))

        self.client.load_collection(CODE)

    def vanilla_embed(self, text: str) -> List[float]:
        """
        Embed a string using the embedding model.
        """
        return self.model.encode(text)

    def __issue_to_embeddable_string(self, issue: Issue) -> str:
        """
        Convert an issue to a string that can be embedded
        """
        return issue.description + " " + " ".join(issue.comments.values())

    def __docu_page_to_embeddable_string(self, page: DocumentationPage) -> str:
        """
        Convert a documentation page to a string that can be embedded
        """
        return f"{page.url} {page.content}"

    def __code_to_embeddable_string(self, code: CodePage) -> str:
        """
        Convert a code to a string that can be embedded
        """
        return code.content

    @typechecked
    def embed(self, data: Union[Issue, DocumentationPage, CodePage]) -> List[float]:
        """
        Embed either an issue or documentation page and return the embedding.

        Args:
            data: Either an Issue or DocumentationPage object to embed

        Returns:
            List[float]: The embedding vector
        """
        if self.is_debug_mode:
            return [0.0] * self.dimension

        if isinstance(data, Issue):
            text = self.__issue_to_embeddable_string(data)
        elif isinstance(data, DocumentationPage):
            text = self.__docu_page_to_embeddable_string(data)
        else:
            text = self.__code_to_embeddable_string(data)

        return self.model.encode(text)

    def add_issue(self, issue: Issue):
        """
        Add a new issue to the vector db.
        """

        # Check if issue already exists
        prev_data = self.client.get(ISSUE, issue.primary_key)
        if len(prev_data) > 0:
            # compare content, if there's even a slight difference, we should update the issue vector.
            prev_data_issue = Issue(**prev_data[0])
            if self.__issue_to_embeddable_string(
                prev_data_issue
            ) == self.__issue_to_embeddable_string(issue):
                return  # Issue content is the same as existing issue, just continue.

        vector = self.embed(issue)
        entity = [
            {
                "primary_key": str(issue.primary_key),
                "vector": vector,
                "description": issue.description,
                "comments": issue.comments,
                "org_id": str(issue.org_id),
            }
        ]

        self.client.upsert(ISSUE, data=entity)

    def get_all_issues(self) -> List[Issue]:
        """
        Get all issues from the vector db
        """
        # Get all primary keys from the collection
        output_fields = ["primary_key", "description", "comments", "org_id", "vector"]
        batch_size = 100
        offset = 0
        all_results = []

        while True:
            results = self.client.query(
                collection_name=ISSUE,
                output_fields=output_fields,
                limit=batch_size,
                offset=offset,
            )

            all_results.extend(results)
            offset += batch_size

            if len(results) < batch_size:
                break

        return [Issue(**issue) for issue in all_results]

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

            issue = Issue(
                primary_key=issue_id,
                description=problem_description,
                comments=comments,
                vector=vector,
                org_id=self.user_id,
            )

            issues[issue_id] = {
                "similarity": distance,
                "metadata": issue.model_dump_json(),
            }

        return issues

    def add_documentation_page(self, doc: DocumentationPage):
        """
        Add documentation page to vector db
        """

        prev_data = self.client.get(DOCUMENTATION, doc.primary_key)
        if len(prev_data) > 0:
            # compare content, if there's even a slight difference, we should update the issue vector.
            prev_data_doc = DocumentationPage(**prev_data[0])
            if self.__docu_page_to_embeddable_string(
                prev_data_doc
            ) == self.__docu_page_to_embeddable_string(doc):
                return  # Page content is the same as existing page, just continue.

        vector = self.embed(doc)
        entity = [
            {
                "primary_key": str(doc.primary_key),
                "vector": vector,
                "url": doc.url,
                "content": doc.content,
                "org_id": str(self.user_id),
            }
        ]

        self.client.upsert(DOCUMENTATION, data=entity)

    def get_all_documentation(self, keys: List[str]) -> List[DocumentationPage]:
        """
        Get all documentation pages from the vector db
        """
        docs = self.client.get(DOCUMENTATION, ids=keys)
        return [DocumentationPage(**doc) for doc in docs]

    def get_top_k_documentation(
        self, k: int, query_vector: List[float]
    ) -> Dict[str, Any]:
        """
        Get top k documentation pages
        """
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = self.client.search(
            collection_name=DOCUMENTATION,
            data=[query_vector],
            anns_field="vector",
            search_params=search_params,
            limit=k,
            output_fields=["vector", "url", "content"],
        )

        docs = {}
        for result in results[0]:
            doc_id = result["id"]
            distance = result["distance"]
            url = result["entity"]["url"]
            content = result["entity"]["content"]
            vector = result["entity"]["vector"]

            doc = DocumentationPage(
                primary_key=doc_id,
                vector=vector,
                org_id=self.user_id,
                url=url,
                content=content,
            )

            docs[doc_id] = {
                "similarity": distance,
                "metadata": doc.model_dump_json(),
            }

        return docs
