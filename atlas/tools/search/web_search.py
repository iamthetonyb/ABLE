"""
Web Search Tool - Search the web via multiple providers.

Supports:
- DuckDuckGo (no API key needed)
- Google Custom Search API
- Bing Search API
- SerpAPI

Returns structured results with title, snippet, URL.
"""

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlencode

logger = logging.getLogger(__name__)

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class SearchProvider(Enum):
    DUCKDUCKGO = "duckduckgo"
    GOOGLE = "google"
    BING = "bing"
    SERPAPI = "serpapi"


@dataclass
class SearchResult:
    """A single search result"""
    title: str
    url: str
    snippet: str
    position: int
    provider: SearchProvider
    metadata: Dict = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Response from a web search"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    provider: SearchProvider


class DuckDuckGoSearch:
    """
    DuckDuckGo search - no API key required.

    Uses the HTML search page and parses results.
    Rate limited to avoid blocks.
    """

    BASE_URL = "https://html.duckduckgo.com/html/"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request = 0
        self._min_delay = 1.0  # seconds between requests

    async def _get_session(self) -> aiohttp.ClientSession:
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp not installed")
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36"
                }
            )
        return self._session

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search DuckDuckGo"""
        if not BS4_AVAILABLE:
            logger.warning("BeautifulSoup not installed, using fallback")
            return []

        # Rate limit
        elapsed = time.time() - self._last_request
        if elapsed < self._min_delay:
            await asyncio.sleep(self._min_delay - elapsed)

        session = await self._get_session()
        self._last_request = time.time()

        try:
            async with session.post(
                self.BASE_URL,
                data={"q": query, "b": ""},
            ) as response:
                if response.status != 200:
                    logger.warning(f"DuckDuckGo returned {response.status}")
                    return []

                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            results = []

            for i, result in enumerate(soup.select('.result')):
                if i >= max_results:
                    break

                title_elem = result.select_one('.result__title a')
                snippet_elem = result.select_one('.result__snippet')

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                # DuckDuckGo uses redirect URLs, extract actual URL
                if 'uddg=' in url:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                    url = parsed.get('uddg', [url])[0]

                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    position=i + 1,
                    provider=SearchProvider.DUCKDUCKGO,
                ))

            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


class GoogleSearch:
    """Google Custom Search API"""

    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(
        self,
        api_key: str = None,
        cx: str = None,  # Custom Search Engine ID
    ):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        self.cx = cx or os.environ.get("GOOGLE_CX", "")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp not installed")
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search Google"""
        if not self.api_key or not self.cx:
            logger.warning("Google API key or CX not configured")
            return []

        session = await self._get_session()

        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": min(max_results, 10),  # Google max is 10
        }

        try:
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.warning(f"Google search failed: {response.status} - {text}")
                    return []

                data = await response.json()

            results = []
            for i, item in enumerate(data.get("items", [])):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    position=i + 1,
                    provider=SearchProvider.GOOGLE,
                    metadata={
                        "displayLink": item.get("displayLink"),
                        "pagemap": item.get("pagemap", {}),
                    }
                ))

            return results

        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


class BingSearch:
    """Bing Search API"""

    BASE_URL = "https://api.bing.microsoft.com/v7.0/search"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("BING_API_KEY", "")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp not installed")
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Ocp-Apim-Subscription-Key": self.api_key}
            )
        return self._session

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search Bing"""
        if not self.api_key:
            logger.warning("Bing API key not configured")
            return []

        session = await self._get_session()

        params = {
            "q": query,
            "count": max_results,
            "textDecorations": "false",
            "textFormat": "Raw",
        }

        try:
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    logger.warning(f"Bing search failed: {response.status}")
                    return []

                data = await response.json()

            results = []
            for i, item in enumerate(data.get("webPages", {}).get("value", [])):
                results.append(SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    position=i + 1,
                    provider=SearchProvider.BING,
                    metadata={
                        "dateLastCrawled": item.get("dateLastCrawled"),
                        "language": item.get("language"),
                    }
                ))

            return results

        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


class WebSearch:
    """
    Unified web search with multiple provider fallback.

    Usage:
        search = WebSearch()
        results = await search.search("ATLAS AI agent")
    """

    def __init__(
        self,
        providers: List[SearchProvider] = None,
        google_api_key: str = None,
        google_cx: str = None,
        bing_api_key: str = None,
    ):
        self.providers = providers or [
            SearchProvider.DUCKDUCKGO,  # Default: no API key needed
        ]

        self._ddg = DuckDuckGoSearch()
        self._google = GoogleSearch(api_key=google_api_key, cx=google_cx)
        self._bing = BingSearch(api_key=bing_api_key)

    async def search(
        self,
        query: str,
        max_results: int = 10,
        provider: SearchProvider = None,
    ) -> SearchResponse:
        """
        Search the web.

        Args:
            query: Search query
            max_results: Maximum results to return
            provider: Specific provider to use (or fallback through all)

        Returns:
            SearchResponse with results
        """
        start_time = time.time()
        providers_to_try = [provider] if provider else self.providers

        for prov in providers_to_try:
            try:
                if prov == SearchProvider.DUCKDUCKGO:
                    results = await self._ddg.search(query, max_results)
                elif prov == SearchProvider.GOOGLE:
                    results = await self._google.search(query, max_results)
                elif prov == SearchProvider.BING:
                    results = await self._bing.search(query, max_results)
                else:
                    continue

                if results:
                    elapsed_ms = (time.time() - start_time) * 1000
                    return SearchResponse(
                        query=query,
                        results=results,
                        total_results=len(results),
                        search_time_ms=elapsed_ms,
                        provider=prov,
                    )

            except Exception as e:
                logger.warning(f"Provider {prov.value} failed: {e}")
                continue

        # All providers failed
        elapsed_ms = (time.time() - start_time) * 1000
        return SearchResponse(
            query=query,
            results=[],
            total_results=0,
            search_time_ms=elapsed_ms,
            provider=providers_to_try[0] if providers_to_try else SearchProvider.DUCKDUCKGO,
        )

    def format_for_llm(self, response: SearchResponse) -> str:
        """Format search results for LLM consumption"""
        if not response.results:
            return f"No results found for: {response.query}"

        lines = [f"Search results for: {response.query}\n"]

        for r in response.results:
            lines.append(f"{r.position}. {r.title}")
            lines.append(f"   URL: {r.url}")
            lines.append(f"   {r.snippet}\n")

        return "\n".join(lines)

    async def close(self):
        """Close all provider sessions"""
        await self._ddg.close()
        await self._google.close()
        await self._bing.close()
