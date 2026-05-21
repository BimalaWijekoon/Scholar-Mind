"""
Web Parser - Extract content from URLs
"""

import httpx
from bs4 import BeautifulSoup
from typing import Dict, Optional
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class WebDocument:
    """Represents a parsed web document."""
    url: str
    title: str
    text: str
    html: str
    metadata: Dict


class WebParser:
    """
    Parser for web documents.
    
    Extracts:
    - Main content text
    - Title
    - Metadata
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the web parser.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def parse(self, url: str) -> WebDocument:
        """
        Parse a web page and extract its contents.
        
        Args:
            url: URL of the web page
            
        Returns:
            WebDocument object with extracted content
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self.headers, follow_redirects=True)
            response.raise_for_status()
            html = response.text
        
        soup = BeautifulSoup(html, "lxml")
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract main content
        text = self._extract_main_content(soup)
        
        # Extract metadata
        metadata = self._extract_metadata(soup, url)
        
        return WebDocument(
            url=url,
            title=title,
            text=text,
            html=html,
            metadata=metadata,
        )
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the page title."""
        # Try different title sources
        if soup.title:
            return soup.title.get_text().strip()
        
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()
        
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "").strip()
        
        return "Untitled"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content text."""
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # Try to find main content area
        main_content = None
        
        # Try common content selectors
        selectors = [
            "article",
            "main",
            ".content",
            ".post-content",
            ".article-content",
            "#content",
            ".entry-content",
        ]
        
        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            # Fall back to body
            body = soup.find("body")
            text = body.get_text(separator="\n", strip=True) if body else ""
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract metadata from the page."""
        metadata = {
            "url": url,
            "domain": urlparse(url).netloc,
        }
        
        # Extract meta tags
        meta_tags = {
            "description": ["description", "og:description"],
            "author": ["author", "article:author"],
            "published_date": ["article:published_time", "datePublished"],
            "keywords": ["keywords"],
        }
        
        for key, names in meta_tags.items():
            for name in names:
                meta = soup.find("meta", attrs={"name": name}) or soup.find("meta", property=name)
                if meta and meta.get("content"):
                    metadata[key] = meta.get("content")
                    break
        
        return metadata
    
    def parse_sync(self, url: str) -> WebDocument:
        """
        Synchronous version of parse.
        
        Args:
            url: URL of the web page
            
        Returns:
            WebDocument object with extracted content
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, headers=self.headers, follow_redirects=True)
            response.raise_for_status()
            html = response.text
        
        soup = BeautifulSoup(html, "lxml")
        
        title = self._extract_title(soup)
        text = self._extract_main_content(soup)
        metadata = self._extract_metadata(soup, url)
        
        return WebDocument(
            url=url,
            title=title,
            text=text,
            html=html,
            metadata=metadata,
        )
