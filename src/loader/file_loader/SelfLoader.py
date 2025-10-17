from typing import List
import os

from langchain_core.documents import Document
from langchain.document_loaders import UnstructuredFileLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from src.loader.file_loader.base import BaseLoader


class SelfLoader(BaseLoader):
    """
    Loader for doc/docx/txt files with automatic summarization capability.

    This loader handles document files with extensions like .doc, .docx, and .txt,
    converting them into Document objects and providing automatic summarization.
    """

    def __init__(self, openai_api_key: str = None, openai_baseurl: str = None, temperature: float = 0):
        """
        Initialize the SelfLoader.

        Args:
            openai_api_key: OpenAI API key for summarization
            temperature: Temperature parameter for OpenAI model (default: 0)
        """
        self.openai_api_key = openai_api_key
        self.temperature = temperature
        
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key

        if openai_baseurl:
            os.environ["OPENAI_API_BASE"] = openai_baseurl

    def load_file(self, file_path: str) -> List[Document]:
        """
        Load a document file and convert it to Document objects.

        Args:
            file_path: Path to the document file to be loaded.

        Returns:
            A list containing a single Document object with the file content and reference.
        """
        loader = UnstructuredFileLoader(file_path)
        documents = loader.load()
        
        # Add reference metadata to each document
        for doc in documents:
            doc.metadata["reference"] = file_path
            
        return documents

    def load_file_with_summary(self, file_path: str) -> List[Document]:
        """
        Load a document file and add summary as metadata.

        Args:
            file_path: Path to the document file to be loaded.

        Returns:
            A list of Document objects with summary included in metadata.
        """
        documents = self.load_file(file_path)
        
        if self.openai_api_key:
            try:
                # Use the already loaded documents instead of reloading
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1500,
                    chunk_overlap=150
                )
                split_docs = text_splitter.split_documents(documents)

                map_prompt = PromptTemplate(
                    template="请总结以下文本:\n\n{text}",
                    input_variables=["text"]
                )
                combine_prompt = PromptTemplate(
                    template="请基于以下摘要，生成一个全面的总结:\n\n{text}",
                    input_variables=["text"]
                )
                llm = ChatOpenAI(model_name="deepseek-chat")
                chain = load_summarize_chain(
                    llm,
                    chain_type="map_reduce",
                    map_prompt=map_prompt,
                    combine_prompt=combine_prompt
                )
                summary = chain.invoke({"input_documents": split_docs})
                
                for doc in documents:
                    doc.metadata["summary"] = summary
            except Exception as e:
                # If summarization fails, still return the documents without summary
                print(f"Summarization failed for {file_path}: {e}")
                for doc in documents:
                    doc.metadata["summary"] = "Summarization unavailable"
        
        return documents

    @property
    def supported_file_types(self) -> List[str]:
        """
        Get the list of file extensions supported by this loader.

        Returns:
            A list of supported file extensions: ["doc", "docx", "txt"].
        """
        return ["doc", "docx", "txt"]


if __name__ == "__main__":

    loader = SelfLoader(openai_api_key="sk-123e9b32a0a34fd48f623c1429241bd8",
                        openai_baseurl="https://api.deepseek.com/v1",
                        temperature=0)
    loader.load_file(
        file_path="/Users/younger/Desktop/yw/myKB/小司/2025-10/[2025-10-09 13-19-44][小司频道][别说了，我是乌鸦嘴😩]_原文.docx")
