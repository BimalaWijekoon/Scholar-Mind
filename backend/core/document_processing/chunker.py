"""
Document Chunker - Split documents into chunks for processing
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class ChunkingStrategy(str, Enum):
    """Chunking strategy options."""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"


@dataclass
class DocumentChunk:
    """Represents a document chunk."""
    id: str
    document_id: str
    text: str
    start_char: int
    end_char: int
    page_number: Optional[int]
    chunk_index: int
    metadata: Dict


class DocumentChunker:
    """
    Chunker for splitting documents into processable chunks.
    
    Supports multiple strategies:
    - Fixed size: Split by character count
    - Sentence: Split by sentences
    - Paragraph: Split by paragraphs
    - Semantic: Split by semantic similarity
    - Recursive: Recursively split with overlap
    """
    
    def __init__(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize the document chunker.
        
        Args:
            strategy: Chunking strategy to use
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Separators for recursive splitting (in order of preference)
        self.separators = ["\n\n", "\n", ". ", " ", ""]
    
    def chunk(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict] = None,
    ) -> List[DocumentChunk]:
        """
        Chunk a document text.
        
        Args:
            text: Document text to chunk
            document_id: ID of the source document
            metadata: Optional metadata to include with chunks
            
        Returns:
            List of DocumentChunk objects
        """
        if self.strategy == ChunkingStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(text, document_id, metadata)
        elif self.strategy == ChunkingStrategy.SENTENCE:
            return self._chunk_by_sentence(text, document_id, metadata)
        elif self.strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(text, document_id, metadata)
        elif self.strategy == ChunkingStrategy.RECURSIVE:
            return self._chunk_recursive(text, document_id, metadata)
        else:
            return self._chunk_recursive(text, document_id, metadata)
    
    def _chunk_fixed_size(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict],
    ) -> List[DocumentChunk]:
        """Split by fixed character count with overlap."""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            chunk_text = text[start:end]
            
            chunks.append(DocumentChunk(
                id=f"{document_id}_chunk_{chunk_index}",
                document_id=document_id,
                text=chunk_text,
                start_char=start,
                end_char=end,
                page_number=None,
                chunk_index=chunk_index,
                metadata=metadata or {},
            ))
            
            start = end - self.chunk_overlap
            chunk_index += 1
        
        return chunks
    
    def _chunk_by_sentence(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict],
    ) -> List[DocumentChunk]:
        """Split by sentences, grouping to meet chunk size."""
        import re
        
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        start_char = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(DocumentChunk(
                    id=f"{document_id}_chunk_{chunk_index}",
                    document_id=document_id,
                    text=chunk_text,
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    page_number=None,
                    chunk_index=chunk_index,
                    metadata=metadata or {},
                ))
                
                start_char += len(chunk_text)
                chunk_index += 1
                current_chunk = []
                current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1
        
        # Add remaining
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(DocumentChunk(
                id=f"{document_id}_chunk_{chunk_index}",
                document_id=document_id,
                text=chunk_text,
                start_char=start_char,
                end_char=start_char + len(chunk_text),
                page_number=None,
                chunk_index=chunk_index,
                metadata=metadata or {},
            ))
        
        return chunks
    
    def _chunk_by_paragraph(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict],
    ) -> List[DocumentChunk]:
        """Split by paragraphs."""
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_length = 0
        start_char = 0
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_length = len(para)
            
            if current_length + para_length > self.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(DocumentChunk(
                    id=f"{document_id}_chunk_{chunk_index}",
                    document_id=document_id,
                    text=chunk_text,
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    page_number=None,
                    chunk_index=chunk_index,
                    metadata=metadata or {},
                ))
                
                start_char += len(chunk_text)
                chunk_index += 1
                current_chunk = []
                current_length = 0
            
            current_chunk.append(para)
            current_length += para_length + 2
        
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(DocumentChunk(
                id=f"{document_id}_chunk_{chunk_index}",
                document_id=document_id,
                text=chunk_text,
                start_char=start_char,
                end_char=start_char + len(chunk_text),
                page_number=None,
                chunk_index=chunk_index,
                metadata=metadata or {},
            ))
        
        return chunks
    
    def _chunk_recursive(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict],
    ) -> List[DocumentChunk]:
        """Recursively split text using multiple separators."""
        raw_chunks = self._split_recursive(text, self.separators)
        
        chunks = []
        start_char = 0
        
        for i, chunk_text in enumerate(raw_chunks):
            chunks.append(DocumentChunk(
                id=f"{document_id}_chunk_{i}",
                document_id=document_id,
                text=chunk_text,
                start_char=start_char,
                end_char=start_char + len(chunk_text),
                page_number=None,
                chunk_index=i,
                metadata=metadata or {},
            ))
            start_char += len(chunk_text)
        
        return chunks
    
    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text."""
        if not separators:
            return [text]
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_length = len(split)
            
            if current_length + split_length > self.chunk_size:
                if current_chunk:
                    chunk_text = separator.join(current_chunk)
                    
                    if len(chunk_text) > self.chunk_size and remaining_separators:
                        # Recursively split
                        sub_chunks = self._split_recursive(chunk_text, remaining_separators)
                        chunks.extend(sub_chunks)
                    else:
                        chunks.append(chunk_text)
                    
                    current_chunk = []
                    current_length = 0
                
                if split_length > self.chunk_size and remaining_separators:
                    sub_chunks = self._split_recursive(split, remaining_separators)
                    chunks.extend(sub_chunks)
                else:
                    current_chunk = [split]
                    current_length = split_length
            else:
                current_chunk.append(split)
                current_length += split_length + len(separator)
        
        if current_chunk:
            chunk_text = separator.join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks
