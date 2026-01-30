from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "briefs.db"


@dataclass
class Article:
    source_id: str
    title: str
    url: str
    published_at: str
    summary: str | None = None


@dataclass
class Brief:
    created_at: str
    highlights: str
    summary: str
    tts_path: str | None = None


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                published_at TEXT NOT NULL,
                summary TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS briefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                highlights TEXT NOT NULL,
                summary TEXT NOT NULL,
                tts_path TEXT
            )
            """
        )


def upsert_articles(articles: Iterable[Article]) -> int:
    inserted = 0
    now = datetime.utcnow().isoformat()
    with connect() as conn:
        for article in articles:
            try:
                conn.execute(
                    """
                    INSERT INTO articles (source_id, title, url, published_at, summary, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article.source_id,
                        article.title,
                        article.url,
                        article.published_at,
                        article.summary,
                        now,
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                continue
    return inserted


def list_articles(limit: int = 100) -> list[sqlite3.Row]:
    with connect() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM articles
            ORDER BY published_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return list(cursor.fetchall())


def save_brief(highlights: str, summary: str, tts_path: str | None) -> None:
    created_at = datetime.utcnow().isoformat()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO briefs (created_at, highlights, summary, tts_path)
            VALUES (?, ?, ?, ?)
            """,
            (created_at, highlights, summary, tts_path),
        )


def latest_brief() -> sqlite3.Row | None:
    with connect() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM briefs
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        return cursor.fetchone()
