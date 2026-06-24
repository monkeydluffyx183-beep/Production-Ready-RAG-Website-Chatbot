"""Text cleaning utilities for web content."""

import re
from html import unescape
from typing import List


def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    # Remove script and style elements
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    return text


def clean_whitespace(text: str) -> str:
    """Clean up whitespace in text."""
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()


def decode_html_entities(text: str) -> str:
    """Decode HTML entities."""
    return unescape(text)


def remove_urls(text: str) -> str:
    """Remove URLs from text."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    text = re.sub(url_pattern, '', text)
    return text


def clean_text(text: str, remove_urls_flag: bool = True) -> str:
    """
    Clean text by removing HTML tags, decoding entities, and normalizing whitespace.
    
    Args:
        text: Raw text to clean
        remove_urls_flag: Whether to remove URLs from text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Decode HTML entities
    text = decode_html_entities(text)
    
    # Remove HTML tags
    text = clean_html_tags(text)
    
    # Optionally remove URLs
    if remove_urls_flag:
        text = remove_urls(text)
    
    # Clean whitespace
    text = clean_whitespace(text)
    
    return text


def extract_title_from_html(html_content: str) -> str:
    """Extract title from HTML content."""
    match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if match:
        return clean_text(match.group(1))
    return "Untitled"


def extract_links_from_html(html_content: str, base_url: str = "") -> List[str]:
    """Extract all links from HTML content."""
    link_pattern = r'href=[\'"]([^\'"]+)[\'"]'
    links = re.findall(link_pattern, html_content, re.IGNORECASE)
    
    # Convert relative URLs to absolute
    if base_url:
        from urllib.parse import urljoin
        links = [urljoin(base_url, link) for link in links]
    
    return links
