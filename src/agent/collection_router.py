from typing import List, Tuple

from src.agent.base import BaseAgent
from src.llm.base import BaseLLM
from src.utils import log
from src.vector_db.base import BaseVectorDB

COLLECTION_ROUTE_PROMPT = """
我为你提供集合名称(collection_name)和对应的集合描述(collection_description)。请选择与问题可能相关的集合名称，并返回一个str类型的python列表。如果没有任何集合与问题相关，你可以返回一个空列表。

"问题": {question}
"集合信息": {collection_info}

在返回时，你只能返回一个str类型的python列表，不能包含任何其他额外内容。你选择的集合名称列表是：
"""


class CollectionRouter(BaseAgent):
    """
    Routes queries to appropriate collections in the vector database.

    This class analyzes the content of a query and determines which collections
    in the vector database are most likely to contain relevant information.
    """

    def __init__(self, llm: BaseLLM, vector_db: BaseVectorDB, dim: int, **kwargs):
        """
        Initialize the CollectionRouter.

        Args:
            llm: The language model to use for analyzing queries.
            vector_db: The vector database containing the collections.
            dim: The dimension of the vector space to search in.
        """
        self.llm = llm
        self.vector_db = vector_db
        self.all_collections = [
            collection_info.collection_name
            for collection_info in self.vector_db.list_collections(dim=dim)
        ]

    def invoke(self, query: str, dim: int, **kwargs) -> Tuple[List[str], int]:
        """
        Determine which collections are relevant for the given query.

        This method analyzes the query content and selects collections that are
        most likely to contain information relevant to answering the query.

        Args:
            query (str): The query to analyze.
            dim (int): The dimension of the vector space to search in.

        Returns:
            Tuple[List[str], int]: A tuple containing:
                - A list of selected collection names
                - The token usage for the routing operation
        """
        consume_tokens = 0
        collection_infos = self.vector_db.list_collections(dim=dim)
        if len(collection_infos) == 0:
            log.warning(
                "No collections found in the vector database. Please check the database connection."
            )
            return [], 0
        if len(collection_infos) == 1:
            the_only_collection = collection_infos[0].collection_name
            log.color_print(
                f"<think> Perform search [{query}] on the vector DB collection: {the_only_collection} </think>\n"
            )
            return [the_only_collection], 0
        vector_db_search_prompt = COLLECTION_ROUTE_PROMPT.format(
            question=query,
            collection_info=[
                {
                    "collection_name": collection_info.collection_name,
                    "collection_description": collection_info.description,
                }
                for collection_info in collection_infos
            ],
        )
        chat_response = self.llm.chat(
            messages=[{"role": "user", "content": vector_db_search_prompt}]
        )
        selected_collections = self.llm.literal_eval(chat_response.content)
        consume_tokens += chat_response.total_tokens

        for collection_info in collection_infos:
            # If a collection description is not provided, use the query as the search query
            if not collection_info.description:
                selected_collections.append(collection_info.collection_name)
            # If the default collection exists, use the query as the search query
            if self.vector_db.default_collection == collection_info.collection_name:
                selected_collections.append(collection_info.collection_name)
        selected_collections = list(set(selected_collections))
        log.color_print(
            f"<think> Perform search [{query}] on the vector DB collections: {selected_collections} </think>\n"
        )
        return selected_collections, consume_tokens
