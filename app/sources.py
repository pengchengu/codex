from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser

from app.storage import Article


@dataclass
class Source:
    id: str
    name: str
    type: str
    url: str


def build_session(user_agent: str, proxy: str | None) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    if proxy:
        session.proxies.update({"http": proxy, "https": proxy})
    return session


def parse_datetime(value: str | None) -> str:
    if not value:
        return datetime.utcnow().isoformat()
    try:
        return parser.parse(value).isoformat()
    except (ValueError, TypeError):
        return datetime.utcnow().isoformat()


def fetch_rss(source: Source, session: requests.Session, max_items: int) -> list[Article]:
    response = session.get(source.url, timeout=20)
    response.raise_for_status()
    feed = feedparser.parse(response.text)
    articles: list[Article] = []
    for entry in feed.entries[:max_items]:
        articles.append(
            Article(
                source_id=source.id,
                title=entry.get("title", "(untitled)"),
                url=entry.get("link", source.url),
                published_at=parse_datetime(entry.get("published")),
                summary=entry.get("summary"),
            )
        )
    return articles


def fetch_html(source: Source, session: requests.Session, max_items: int) -> list[Article]:
    response = session.get(source.url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    articles: list[Article] = []
    for anchor in soup.select("a")[: max_items * 3]:
        title = anchor.get_text(strip=True)
        url = anchor.get("href")
        if not title or not url:
            continue
        if url.startswith("/"):
            url = source.url.rstrip("/") + url
        articles.append(
            Article(
                source_id=source.id,
                title=title,
                url=url,
                published_at=datetime.utcnow().isoformat(),
                summary=None,
            )
        )
        if len(articles) >= max_items:
            break
    return articles


def fetch_sources(
    sources: Iterable[Source],
    user_agent: str,
    proxy: str | None,
    max_items: int,
) -> list[Article]:
    session = build_session(user_agent, proxy)
    results: list[Article] = []
    for source in sources:
        if source.type == "rss":
            results.extend(fetch_rss(source, session, max_items))
        else:
            results.extend(fetch_html(source, session, max_items))
    return results
