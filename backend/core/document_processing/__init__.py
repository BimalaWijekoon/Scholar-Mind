"""
Document Processing Module
"""

from backend.core.document_processing.pdf_parser import PDFParser
from backend.core.document_processing.web_parser import WebParser
from backend.core.document_processing.metadata_extractor import MetadataExtractor
from backend.core.document_processing.chunker import DocumentChunker

__all__ = ["PDFParser", "WebParser", "MetadataExtractor", "DocumentChunker"]
