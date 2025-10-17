from src.loader.file_loader.docling_loader import DoclingLoader
from src.loader.file_loader.json_loader import JsonFileLoader
from src.loader.file_loader.pdf_loader import PDFLoader
from src.loader.file_loader.text_loader import TextLoader
from src.loader.file_loader.unstructured_loader import UnstructuredLoader
from src.loader.file_loader.SelfLoader import SelfLoader

__all__ = ["PDFLoader", "TextLoader", "UnstructuredLoader", "JsonFileLoader", "DoclingLoader", "SelfLoader"]
