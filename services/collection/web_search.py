"""Strategic OSIRIS - Real-Time Web Search & Open-Source Intelligence Client.
Provides live open-source web and news search capabilities using resilient multi-tier providers:
1. Google News RSS Feeds (bilingual Arabic/English, instant, zero-key, high-reliability media)
2. DuckDuckGo / ddgs search fallback
Converts raw web results into standardized Admiralty-scored DocumentEvidence items.
"""
from __future__ import annotations

import asyncio
import logging
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
import httpx
from packages.schemas.models import AdmiraltyCredibility, AdmiraltyReliability, DocumentEvidence
from services.collection.evidence_metadata import canonical_url, content_hash, evidence_id, publication_date

log = logging.getLogger("strategic_osiris.web_search")


class WebSearchClient:
    """Asynchronous Web Search client providing real-time live open-source intelligence."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def _is_arabic(self, text: str) -> bool:
        """Check if query contains Arabic script."""
        return bool(re.search(r"[\u0600-\u06FF]", text))

    def _fetch_rss_items(self, query: str, lang: str = "ar", max_results: int = 5) -> List[Dict[str, Any]]:
        """Query Google News RSS for live, up-to-the-minute news reporting."""
        results: List[Dict[str, Any]] = []
        encoded = urllib.parse.quote(query)

        if lang == "ar":
            url = f"https://news.google.com/rss/search?q={encoded}&hl=ar&gl=EG&ceid=EG:ar"
        else:
            url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        }

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return []
                root = ET.fromstring(resp.text)
                for item in root.findall(".//item")[:max_results]:
                    raw_title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub_str = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    
                    # Clean title and separate publisher source
                    clean_desc = re.sub(r"<[^<]+?>", "", desc).strip()
                    source = "Google News"
                    clean_title = raw_title
                    if " - " in raw_title:
                        parts = raw_title.rsplit(" - ", 1)
                        clean_title = parts[0].strip()
                        source = parts[1].strip()

                    # Parse pub date
                    dt = publication_date(pub_str)

                    results.append({
                        "title": clean_title,
                        "source": source,
                        "url": link,
                        "body": clean_desc or clean_title,
                        "date": dt.isoformat() if dt else None,
                        "datetime": dt
                    })
        except Exception as e:
            log.warning("RSS news search failed for query '%s' (%s): %s", query, lang, e)

        return results

    def _sync_ddg_fallback(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """DuckDuckGo secondary search fallback."""
        try:
            from ddgs import DDGS
            with DDGS(timeout=int(self.timeout)) as ddgs:
                results = []
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "source": "Web Search",
                        "url": r.get("href", ""),
                        "body": r.get("body", ""),
                        "date": "",
                        "datetime": None
                    })
                return results
        except Exception:
            return []

    async def search(self, query: str, max_results: int = 6) -> List[Dict[str, Any]]:
        """Perform non-blocking live multi-source web and news search."""
        is_ar = self._is_arabic(query)
        primary_lang = "ar" if is_ar else "en"
        secondary_lang = "en" if is_ar else "ar"

        # 1. Primary news RSS search
        items = await asyncio.to_thread(self._fetch_rss_items, query, primary_lang, max_results)

        # 2. If results are few, try secondary language
        if len(items) < max_results:
            more_items = await asyncio.to_thread(self._fetch_rss_items, query, secondary_lang, max_results - len(items))
            items.extend(more_items)

        # 3. If still empty, try DDG fallback
        if not items:
            ddg_items = await asyncio.to_thread(self._sync_ddg_fallback, query, max_results)
            items.extend(ddg_items)

        # Deduplicate by URL and title
        seen = set()
        deduped = []
        for it in items:
            key = it.get("url") or it.get("title")
            if key and key not in seen:
                seen.add(key)
                deduped.append(it)
            if len(deduped) >= max_results:
                break

        return deduped

    async def search_as_evidence(
        self,
        query: str,
        target_countries: Optional[List[str]] = None,
        max_results: int = 5
    ) -> List[DocumentEvidence]:
        """Search the web and convert results into unverified evidence records."""
        raw_items = await self.search(query, max_results=max_results)
        evidences: List[DocumentEvidence] = []
        target_countries = target_countries or ["Egypt", "Libya", "Israel"]

        for item in raw_items:
            title = item.get("title", "").strip()
            body = item.get("body", "").strip()
            url = canonical_url(item.get("url"))
            source_name = item.get("source", "Open Media")
            dt = publication_date(item.get("datetime") or item.get("date"))

            if not title:
                continue

            # Detect mentioned countries
            combined = f"{title} {body}".lower()
            detected = []
            if any(k in combined for k in ("egypt", "cairo", "suez", "sinai", "مصر", "القاهرة")):
                detected.append("Egypt")
            if any(k in combined for k in ("libya", "tripoli", "benghazi", "ليبيا", "طرابلس", "بنغازي")):
                detected.append("Libya")
            if any(k in combined for k in ("israel", "tel aviv", "gaza", "palestin", "إسرائيل", "غزة")):
                detected.append("Israel")
            if any(k in combined for k in ("red sea", "yemen", "houthi", "bab el-mandeb", "البحر الأحمر")):
                detected.append("Red Sea")
            if not detected:
                detected = ["Regional"]

            # Generate stable ID hash
            doc_id = evidence_id("WEB", url, f"{source_name}:{title}")

            doc = DocumentEvidence(
                id=doc_id,
                source_id=doc_id.replace("EVD-", "SRC-", 1),
                source_name=f"Live Media / {source_name}",
                title=title,
                url=url,
                content_snippet=body[:450] if body else title,
                reliability=AdmiraltyReliability.C,  # C: Fairly Reliable (Open Media)
                credibility=AdmiraltyCredibility.TWO,  # 2: Probably True
                countries_mentioned=detected,
                tags=["live_web_search", "osint"],
                published_at=dt,
                content_hash=content_hash(title, body[:450] if body else title),
            )
            evidences.append(doc)

        return evidences
