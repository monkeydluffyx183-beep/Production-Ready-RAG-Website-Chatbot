import re
from bs4 import BeautifulSoup


def clean_html(html: str) -> tuple[str, str]:
    """Return (title, cleaned_text) from raw HTML."""
    soup = BeautifulSoup(html, "lxml")

    # Drop non-content tags
    for tag in soup(["script", "style", "noscript", "iframe", "svg",
                     "header", "footer", "nav", "aside"]):
        tag.decompose()

    title = (soup.title.string if soup.title else "").strip()

    # Prefer <main>/<article> if present
    main = soup.find("main") or soup.find("article") or soup.body
    text = main.get_text(separator="\n", strip=True) if main else ""

    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return title, text.strip()


def is_meaningful(text: str, min_chars: int = 200) -> bool:
    if not text or len(text) < min_chars:
        return False
    alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / len(text)
    return alpha_ratio > 0.7
