from include.constants import (
    DOCUMENTATION,
    ISSUE,
    RUNBOOK,
    CODE,
    NVIDIA_EMBED,
    OPENAI_EMBED,
    DIMENSION_OPENAI,
    DIMENSION_NVIDIA,
    SUPPORTED_MODELS,
    VOYAGE_CODE_EMBED,
    DIMENSION_VOYAGE,
)
from pymilvus import DataType, CollectionSchema, FieldSchema
from src.model.documentation import DocumentationPage
from sentence_transformers import SentenceTransformer
from pymilvus.milvus_client.index import IndexParams
from typing import List, Any, Dict, Union, Optional
from src.storage.supa import SupaClient
from src.model.code import CodePage, CodePageType
from src.model.issue import Comment
from pymilvus import MilvusClient
from typeguard import typechecked
import traceback
import logging
import json
import voyageai
from src.model.issue import Issue
from dotenv import load_dotenv
from openai import OpenAI
from uuid import UUID
import os

PRIMARY_KEY_FIELD = "primary_key"

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
        elif name.lower() == VOYAGE_CODE_EMBED.lower():
            return voyageai.Client(api_key=os.environ.get("VOYAGE_API_KEY"))
        else:
            raise ValueError(
                f"embedding model not supported. Choose one of {','.join(SUPPORTED_MODELS)}"
            )

    def encode(self, text: str, input_type: Optional[str] = None) -> List[List[float]]:
        """
        Encode the provided string.

        Args:
            text: The string to encode
            input_type: The type of input to encode, one of "document" or "query". Defaults to None. Only for voyage.
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
        elif self.model_name.lower() == VOYAGE_CODE_EMBED.lower():
            return self.client.embed(
                [text],
                model=self.model_name,
                input_type=input_type,
                output_dimension=DIMENSION_VOYAGE,
            ).embeddings[0]
        else:
            raise ValueError(
                f"embedding model not supported. Choose one of {','.join(SUPPORTED_MODELS)}"
            )


# VectorDB class wrapping Milvus client and an embedding model
class VectorDB:
    """
    Wrapper around vector db interactions
    """

    def __init__(
        self,
        user_id: UUID,
        embedding_model_name: str = VOYAGE_CODE_EMBED,
        dimension: int = DIMENSION_VOYAGE,
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
        self.chunk_size = 8192

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
                name=PRIMARY_KEY_FIELD,
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=36,
            ),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(
                name="comments",
                dtype=DataType.ARRAY,
                element_type=DataType.VARCHAR,
                max_capacity=36,
                max_length=65535,
            ),
            FieldSchema(name="org_id", dtype=DataType.VARCHAR, max_length=36),
            FieldSchema(name="ticket_number", dtype=DataType.VARCHAR, max_length=36),
            FieldSchema(
                name="metadata", dtype=DataType.JSON
            ),  # TODO remove this when the issue table becomes set in stone. This is for backwards compatibility in case we need to add new fields.
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
                name=PRIMARY_KEY_FIELD,
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
                name=PRIMARY_KEY_FIELD,
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=1024,
            ),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="org_id", dtype=DataType.VARCHAR, max_length=36),
            FieldSchema(name="page_type", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="sha", dtype=DataType.VARCHAR, max_length=64),
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
        Convert an issue to a string that can be embedded.
        """
        return (
            issue.description
            + " "
            + json.dumps([comment.model_dump_json() for comment in issue.comments])
        )

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
        Add a new issue to the vector db by splitting it into chunks.
        """
        chunks = self.__chunk_data(self.__issue_to_embeddable_string(issue))

        for i, chunk in enumerate(chunks):
            chunk_key = f"{issue.primary_key}-{i}"
            prev_data = self.client.get(ISSUE, chunk_key)
            if len(prev_data) > 0:
                # Need to load comments in to comply with Issue model
                comments = [
                    Comment.model_validate_json(comment_json)
                    for comment_json in prev_data[0]["comments"]
                ]
                prev_data[0]["comments"] = comments
                prev_data_issue = Issue(**prev_data[0])

                # compare content, if there's even a slight difference, we should update the issue vector.
                if self.__issue_to_embeddable_string(prev_data_issue) == chunk:
                    continue

            try:
                vector = self.vanilla_embed(chunk)
            except Exception as e:
                logging.error(f"Failed to embed chunk {i}: {str(e)}")
                logging.error(traceback.format_exc())

            entity = [
                {
                    PRIMARY_KEY_FIELD: f"{issue.primary_key}-{i}",
                    "vector": vector,
                    "description": issue.description,
                    "comments": [
                        comment.model_dump_json() for comment in issue.comments
                    ],
                    "org_id": str(issue.org_id),
                    "ticket_number": issue.ticket_number,
                    "metadata": {},  # Nothing for now, but we can add new fields here in the future.
                }
            ]

            self.client.upsert(ISSUE, data=entity)

    def get_all_issues(self, filter_by_org_id: bool = True) -> List[Issue]:
        """
        Get all issues from the vector db
        """
        # Get all primary keys from the collection
        output_fields = [
            PRIMARY_KEY_FIELD,
            "description",
            "comments",
            "org_id",
            "vector",
            "ticket_number",
        ]
        batch_size = 100
        offset = 0
        all_results = []

        while True:
            filter = f"org_id == '{str(self.user_id)}'" if filter_by_org_id else ""
            results = self.client.query(
                collection_name=ISSUE,
                output_fields=output_fields,
                limit=batch_size,
                offset=offset,
                filter=filter,
            )

            all_results.extend(results)
            offset += batch_size

            if len(results) < batch_size:
                break

        retval = []
        for issue in all_results:
            issue["comments"] = [
                Comment.model_validate_json(comment_json)
                for comment_json in issue["comments"]
            ]
            retval.append(Issue(**issue))

        return retval

    def get_top_k_issues(self, k: int, query_vector: List[float]) -> Dict[str, Any]:
        """
        Get top k issues matching the org_id of this vector db instance
        """
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

        # TODO enforce org id filter over search for this and other collections.
        filter = f'org_id == "{str(self.user_id)}"'
        results = self.client.search(
            collection_name=ISSUE,
            data=[query_vector],
            anns_field="vector",
            search_params=search_params,
            limit=k,
            output_fields=[
                "vector",
                "description",
                "comments",
                "org_id",
                "ticket_number",
            ],
            filter=filter,
        )

        issues = {}
        for result in results[
            0
        ]:  # TODO make sure we're returning the ticket number correctly, not doing that right at the moment. The primary key is returned, and the ticket number is null.
            issue_id = result["id"]
            distance = result["distance"]
            problem_description = result["entity"]["description"]
            comments = result["entity"]["comments"]
            vector = result["entity"]["vector"]
            ticket_number = result["entity"]["ticket_number"]

            loaded_comments = [
                Comment.model_validate_json(comment_json) for comment_json in comments
            ]
            issue = Issue(
                primary_key=issue_id,
                description=problem_description,
                comments=loaded_comments,
                vector=vector,
                org_id=self.user_id,
                ticket_number=ticket_number,
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
                PRIMARY_KEY_FIELD: str(doc.primary_key),
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
        filter = f"org_id == '{str(self.user_id)}'"
        results = self.client.search(
            collection_name=DOCUMENTATION,
            data=[query_vector],
            anns_field="vector",
            search_params=search_params,
            limit=k,
            output_fields=["vector", "url", "content"],
            filter=filter,
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

    def __chunk_data(self, content: str) -> List[str]:
        """
        Chunk the data into several smaller chunks, each of character length of num_tokens_from_string(content, self.model.model_name).
        """
        chunks = [
            content[i : i + self.chunk_size]
            for i in range(0, len(content), self.chunk_size)
        ]
        return chunks

    def add_code_file(self, file: CodePage):
        """
        Add a code file to the vector db
        """
        chunks = self.__chunk_data(file.content)

        for i, chunk in enumerate(chunks):
            chunk_key = f"{file.primary_key}-{i}"

            try:
                prev_data = self.client.get(CODE, chunk_key)
            except Exception as e:
                logging.error(f"Failed to get previous data for {chunk_key}: {str(e)}")
                # logging.error(traceback.format_exc())
                prev_data = []

            if len(prev_data) > 0:
                # compare content, if there's even a slight difference, we should update the code vector.
                prev_data_code = CodePage(**prev_data[0])
                if (
                    self.__code_to_embeddable_string(prev_data_code) == chunk
                ):  # This is ok so long as the code to embeddable string is just the content.
                    continue

            try:
                vector = self.vanilla_embed(chunk)
            except Exception as e:
                logging.error(f"Failed to embed chunk {i}: {str(e)}")
                logging.error(traceback.format_exc())

            entity = [
                {
                    PRIMARY_KEY_FIELD: f"{file.primary_key}-{i}",
                    "vector": vector,
                    "content": chunk,
                    "org_id": str(file.org_id),
                    "page_type": file.page_type.value,
                    "sha": file.sha,
                }
            ]

            self.client.upsert(CODE, data=entity)

    def get_top_k_code(self, k: int, query_vector: List[float]) -> Dict[str, Any]:
        """
        Get top k code files
        """
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        filter = f"org_id == '{str(self.user_id)}'"
        results = self.client.search(
            collection_name=CODE,
            data=[query_vector],
            anns_field="vector",
            search_params=search_params,
            limit=k,
            output_fields=["vector", "content", "org_id", "page_type", "sha"],
            filter=filter,
        )

        code = {}
        for result in results[0]:
            code_id = result["id"]
            distance = result["distance"]
            content = result["entity"]["content"]
            org_id = result["entity"]["org_id"]
            page_type = result["entity"]["page_type"]
            vector = result["entity"]["vector"]
            sha = result["entity"]["sha"]

            code_file = CodePage(
                primary_key=code_id,
                vector=vector,
                org_id=org_id,
                content=content,
                page_type=page_type,
                sha=sha,
            )

            code[code_id] = {
                "similarity": distance,
                "metadata": code_file.model_dump_json(),
            }

        return code

    def get_code_pages(self, filename_filter: Optional[str] = None) -> List[CodePage]:
        """
        Get all code pages from the vector db
        """
        # Get all primary keys from the collection
        output_fields = [PRIMARY_KEY_FIELD, "content", "org_id", "page_type", "sha"]
        batch_size = 100
        offset = 0
        all_results = []
        expr = f"page_type == '{CodePageType.CODE.value}' and org_id == '{str(self.user_id)}'"
        if filename_filter is not None:
            expr += f' and {PRIMARY_KEY_FIELD} like "%{filename_filter}%"'

        while True:
            results = self.client.query(
                collection_name=CODE,
                output_fields=output_fields,
                limit=batch_size,
                offset=offset,
                filter=expr,
            )

            all_results.extend(results)
            offset += batch_size

            if len(results) < batch_size:
                break

        return [CodePage(**code) for code in all_results]
