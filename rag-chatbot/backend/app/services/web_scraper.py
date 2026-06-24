"""Web scraping service for crawling websites."""

import asyncio
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from langchain.schema import Document

from app.utils.text_cleaner import clean_text, extract_title_from_html, extract_links_from_html
from app.core.config import settings


class WebScraper:
    """Recursive web scraper for content extraction."""
    
    def __init__(
        self,
        max_pages: int = 50,
        max_depth: int = 3,
        request_timeout: int = 10,
        same_domain_only: bool = True
    ):
        """
        Initialize web scraper.
        
        Args:
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth of recursion
            request_timeout: Timeout for HTTP requests in seconds
            same_domain_only: Only crawl pages on the same domain
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.request_timeout = request_timeout
        self.same_domain_only = same_domain_only
        self.visited_urls: Set[str] = set()
        self.documents: List[Document] = []
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc
    
    def _is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid for crawling."""
        if url in self.visited_urls:
            return False
        
        # Check same domain constraint
        if self.same_domain_only:
            url_domain = self._get_domain(url)
            if url_domain != base_domain:
                return False
        
        # Skip common non-content URLs
        skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg', '.css', '.js']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        return True
    
    async def _fetch_page(
        self,
        session: aiohttp.ClientSession,
        url: str,
        depth: int,
        base_domain: str,
        progress_callback: Optional[callable] = None
    ) -> None:
        """Fetch a single page and extract content."""
        if len(self.visited_urls) >= self.max_pages or depth > self.max_depth:
            return
        
        if not self._is_valid_url(url, base_domain):
            return
        
        self.visited_urls.add(url)
        
        try:
            async with session.get(url, timeout=self.request_timeout) as response:
                if response.status != 200:
                    return
                
                html_content = await response.text()
                
                # Parse HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract title
                title = extract_title_from_html(html_content)
                
                # Extract main content (simplified - could be enhanced)
                # Remove script and style tags
                for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()
                
                # Get text content
                text_content = soup.get_text(separator='\n', strip=True)
                cleaned_text = clean_text(text_content)
                
                if cleaned_text:
                    # Create document
                    doc = Document(
                        page_content=cleaned_text,
                        metadata={
                            "source": url,
                            "title": title,
                            "crawled_at": datetime.utcnow().isoformat(),
                            "depth": depth
                        }
                    )
                    self.documents.append(doc)
                    
                    if progress_callback:
                        await progress_callback(len(self.visited_urls), self.max_pages)
                
                # Extract links for recursive crawling
                if depth < self.max_depth:
                    links = extract_links_from_html(html_content, url)
                    
                    # Create tasks for child pages
                    tasks = []
                    for link in links:
                        if self._is_valid_url(link, base_domain):
                            task = self._fetch_page(
                                session, link, depth + 1, base_domain, progress_callback
                            )
                            tasks.append(task)
                    
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            pass
    
    async def crawl(
        self,
        url: str,
        progress_callback: Optional[callable] = None
    ) -> List[Document]:
        """
        Recursively crawl a website and extract content.
        
        Args:
            url: Starting URL to crawl
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of extracted documents
        """
        self.visited_urls.clear()
        self.documents.clear()
        
        base_domain = self._get_domain(url)
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(10)
        
        async def limited_fetch(session, url, depth, domain, callback):
            async with semaphore:
                await self._fetch_page(session, url, depth, domain, callback)
        
        async with aiohttp.ClientSession() as session:
            await limited_fetch(session, url, 0, base_domain, progress_callback)
        
        return self.documents
    
    def crawl_sync(
        self,
        url: str,
        progress_callback: Optional[callable] = None
    ) -> List[Document]:
        """Synchronous wrapper for crawl method."""
        return asyncio.run(self.crawl(url, progress_callback))
