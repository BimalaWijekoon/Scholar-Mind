"""
Metadata Extractor - Extract title, authors, abstract from documents
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DocumentMetadata:
    """Document metadata."""
    title: str
    authors: List[str]
    abstract: Optional[str]
    publication_date: Optional[str]
    doi: Optional[str]
    keywords: List[str]
    references_count: int


class MetadataExtractor:
    """
    Extractor for document metadata.
    
    Uses heuristics and patterns to extract:
    - Title
    - Authors
    - Abstract
    - Publication date
    - DOI
    - Keywords
    """
    
    def __init__(self):
        """Initialize the metadata extractor."""
        # Patterns for metadata extraction
        self.doi_pattern = re.compile(r'10\.\d{4,}/[^\s]+')
        self.email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
        self.year_pattern = re.compile(r'\b(19|20)\d{2}\b')
        
    def extract(self, text: str, pdf_metadata: Optional[Dict] = None) -> DocumentMetadata:
        """
        Extract metadata from document text.
        
        Args:
            text: Document text content
            pdf_metadata: Optional PDF metadata dict
            
        Returns:
            DocumentMetadata object
        """
        # Split text into lines for analysis
        lines = text.split('\n')
        
        # Extract title
        title = self._extract_title(lines, pdf_metadata)
        
        # Extract authors
        authors = self._extract_authors(lines, text)
        
        # Extract abstract
        abstract = self._extract_abstract(text)
        
        # Extract DOI
        doi = self._extract_doi(text)
        
        # Extract publication date
        pub_date = self._extract_publication_date(text, pdf_metadata)
        
        # Extract keywords
        keywords = self._extract_keywords(text)
        
        # Count references
        ref_count = self._count_references(text)
        
        return DocumentMetadata(
            title=title,
            authors=authors,
            abstract=abstract,
            publication_date=pub_date,
            doi=doi,
            keywords=keywords,
            references_count=ref_count,
        )
    
    def _extract_title(self, lines: List[str], pdf_metadata: Optional[Dict]) -> str:
        """Extract the document title."""
        # Try PDF metadata first
        if pdf_metadata and pdf_metadata.get("title"):
            title = pdf_metadata["title"].strip()
            if len(title) > 5:
                return title
        
        # Look for title in first few lines
        for line in lines[:20]:
            line = line.strip()
            # Title is usually one of the first non-empty lines
            # and is typically longer than 10 characters but not too long
            if 10 < len(line) < 200:
                # Avoid lines that look like headers or metadata
                if not any(skip in line.lower() for skip in ['abstract', 'introduction', 'http', '@']):
                    return line
        
        return "Untitled Document"
    
    def _extract_authors(self, lines: List[str], text: str) -> List[str]:
        """Extract author names."""
        authors = []
        
        # Look for author section
        in_author_section = False
        author_lines = []
        
        for i, line in enumerate(lines[:50]):
            line = line.strip()
            
            # Start of author section
            if 'author' in line.lower() and len(line) < 30:
                in_author_section = True
                continue
            
            # End of author section
            if in_author_section:
                if any(word in line.lower() for word in ['abstract', 'introduction', 'keywords']):
                    break
                if line and not self.email_pattern.search(line):
                    author_lines.append(line)
        
        # Parse author lines
        for line in author_lines[:10]:
            # Split by common separators
            parts = re.split(r'[,;]|\band\b', line)
            for part in parts:
                part = part.strip()
                # Basic validation: author names usually have 2-4 words
                words = part.split()
                if 2 <= len(words) <= 5 and all(w[0].isupper() for w in words if w):
                    authors.append(part)
        
        return authors[:20]  # Limit to 20 authors
    
    def _extract_abstract(self, text: str) -> Optional[str]:
        """Extract the abstract."""
        # Look for abstract section
        abstract_patterns = [
            r'abstract[:\s]*\n(.+?)(?=\n\s*(?:introduction|keywords|1\.|1\s+introduction))',
            r'abstract[:\s]+(.+?)(?=\n\s*(?:introduction|keywords|1\.))',
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                # Clean up whitespace
                abstract = ' '.join(abstract.split())
                if len(abstract) > 100:
                    return abstract[:2000]  # Limit length
        
        return None
    
    def _extract_doi(self, text: str) -> Optional[str]:
        """Extract DOI."""
        match = self.doi_pattern.search(text)
        if match:
            return match.group(0)
        return None
    
    def _extract_publication_date(self, text: str, pdf_metadata: Optional[Dict]) -> Optional[str]:
        """Extract publication date."""
        # Try PDF metadata
        if pdf_metadata:
            for key in ['creationDate', 'modDate']:
                if pdf_metadata.get(key):
                    return pdf_metadata[key]
        
        # Look for year in text
        years = self.year_pattern.findall(text[:5000])
        if years:
            return years[0]
        
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords."""
        keywords = []
        
        # Look for keywords section
        pattern = r'keywords?[:\s]+(.+?)(?=\n\s*(?:1\.|introduction|abstract)|\n\n)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            keyword_text = match.group(1)
            # Split by common separators
            parts = re.split(r'[,;•·]|\n', keyword_text)
            for part in parts:
                part = part.strip()
                if 2 < len(part) < 50:
                    keywords.append(part)
        
        return keywords[:15]  # Limit to 15 keywords
    
    def _count_references(self, text: str) -> int:
        """Count the number of references."""
        # Look for references section
        ref_section = re.search(
            r'(?:references|bibliography)\s*\n(.+)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if ref_section:
            ref_text = ref_section.group(1)
            # Count numbered references
            numbered = len(re.findall(r'^\s*\[\d+\]', ref_text, re.MULTILINE))
            if numbered > 0:
                return numbered
            
            # Count by line breaks or DOIs
            dois = len(self.doi_pattern.findall(ref_text))
            if dois > 0:
                return dois
        
        return 0
