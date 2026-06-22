from __future__ import annotations
import asyncio
import logging
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

import httpx
import tldextract
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.text import clean_html, is_meaningful

logger = logging.getLogger(__name__)


@dataclass
class Page:
    url: str
    title: str
    text: str


class SiteCrawler:
    def __init__(self, seed_url: str, max_pages: int | None = None):
        settings = get_settings()
        self.seed = str(seed_url)
        self.seed_domain = tldextract.extract(self.seed).registered_domain
        self.max_pages = max_pages or settings.max_pages
        self.timeout = settings.request_timeout
        self.headers = {"User-Agent": settings.user_agent}
        self.visited: set[str] = set()
        self.results: list[Page] = []

    def _same_site(self, url: str) -> bool:
        return tldextract.extract(url).registered_domain == self.seed_domain

    def _normalize(self, url: str) -> str:
        p = urlparse(url)
        # drop fragment
        return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/") + (
            f"?{p.query}" if p.query else ""
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _fetch(self, client: httpx.AsyncClient, url: str) -> str | None:
        resp = await client.get(url, follow_redirects=True, timeout=self.timeout)
        if resp.status_code != 200:
            return None
        ct = resp.headers.get("content-type", "")
        if "text/html" not in ct:
            return None
        return resp.text

    async def run(self) -> list[Page]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            queue: asyncio.Queue[str] = asyncio.Queue()
            await queue.put(self.seed)
            self.visited.add(self.seed)

            async def worker():
                while True:
                    url = await queue.get()
                    if url is None:
                        break
                    try:
                        html = await self._fetch(client, url)
                        if not html:
                            continue
                        title, text = clean_html(html)
                        if is_meaningful(text):
                            self.results.append(Page(url=url, title=title, text=text))
                            logger.info("Indexed %s (%d chars)", url, len(text))

                        if len(self.visited) >= self.max_pages:
                            continue

                        # Extract same-site links
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, "lxml")
                        for a in soup.find_all("a", href=True):
                            href = urljoin(url, a["href"])
                            href = self._normalize(href)
                            if (
                                self._same_site(href)
                                and href not in self.visited
                                and not any(ext in href for ext in
                                            (".pdf", ".png", ".jpg", ".zip"))
                            ):
                                self.visited.add(href)
                                await queue.put(href)
                    except Exception as e:
                        logger.warning("Failed %s: %s", url, e)
                    finally:
                        queue.task_done()

            workers = [asyncio.create_task(worker()) for _ in range(5)]
            await queue.join()
            for _ in workers:
                await queue.put(None)
            await asyncio.gather(*workers)

        return self.results
