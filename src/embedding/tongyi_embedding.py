from typing import List

from src.embedding.base import BaseEmbedding

class QwenEmbedding(BaseEmbedding):
    """
    Qwen embedding model implementation.

    This class provides an interface to the Qwen embedding API, which offers
    various embedding models for text processing.

    For more information, see:
    https://help.aliyun.com/zh/model-studio/embedding
    """

    def __init__(self, **kwargs):
        """
        Initialize the Qwen embedding model.

        Args:
            model (str): The model identifier to use for embeddings. Default is "text-embedding-ada-002".
            **kwargs: Additional keyword arguments.
                - api_key (str, optional): The OpenAI API key. If not provided,
                  it will be read from the OPENAI_API_KEY environment variable.
                - base_url (str, optional): The base URL for the OpenAI API. If not provided,
                  it will be read from the OPENAI_BASE_URL environment variable.
                - model_name (str, optional): Alternative way to specify the model.
                - dimension (int, optional): The dimension of the embedding vectors.
                  If not provided, the default dimension for the model will be used.
                - azure_endpoint (str, optional): If provided, use Azure OpenAI instead.
                - api_version (str, optional): Azure API version to use. Default is "2023-05-15".

        Notes:
            Available models:
                - 'text-embedding-ada-002': No dimension needed, default is 1536
                - 'text-embedding-3-small': dimensions from 512 to 1536, default is 1536
                - 'text-embedding-3-large': dimensions from 1024 to 3072, default is 3072
        """
        api_key = "sk-f66bceff0275471594c2a3e17096c94d"
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        self.dim = 1024
        self.model = "text-embedding-v4"

        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _get_dim(self):
        """
        Get the dimension parameter for the API call.

        Returns:
            int or NOT_GIVEN: The dimension to use for the embedding, or NOT_GIVEN
            if using text-embedding-ada-002 which doesn't support custom dimensions.
        """
        return self.dim

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text (str): The query text to embed.

        Returns:
            List[float]: A list of floats representing the embedding vector.
        """
        response = self.client.embeddings.create(
            input=[text], model=self.model, dimensions=self._get_dim()
        )

        return response.data[0].embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of document texts.

        Args:
            texts (List[str]): A list of document texts to embed.

        Returns:
            List[List[float]]: A list of embedding vectors, one for each input text.
        """
        response = self.client.embeddings.create(
            input=texts, model=self.model, dimensions=self._get_dim()
        )

        return [r.embedding for r in response.data]

    @property
    def dimension(self) -> int:
        """
        Get the dimensionality of the embeddings for the current model.

        Returns:
            int: The number of dimensions in the embedding vectors.
        """
        return self.dim


if __name__ == "__main__":
    embedding = QwenEmbedding()
    print(embedding.embed_query("hello world"))
    print(embedding.embed_documents(["hello world", "hello world"]))
