from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

import requests

from app.storage import Article


@dataclass
class SummaryResult:
    highlights: list[str]
    summary: str


def default_summary(articles: Iterable[Article], highlight_count: int) -> SummaryResult:
    titles = [article.title for article in articles]
    highlights = titles[:highlight_count]
    summary = "\n".join(f"- {title}" for title in highlights)
    if not summary:
        summary = "暂无可用内容。"
    return SummaryResult(highlights=highlights, summary=summary)


def build_prompt(articles: Iterable[Article], highlight_count: int) -> str:
    payload = [
        {
            "title": article.title,
            "url": article.url,
            "published_at": article.published_at,
            "summary": article.summary,
        }
        for article in articles
    ]
    return (
        "你是金融新闻晨报助手。请根据以下新闻列表，挑选"
        f"{highlight_count}条重点，用简洁中文输出：\n"
        "1) highlights: 每条不超过25字\n"
        "2) summary: 80-160字的早报摘要\n"
        "数据如下：\n"
        + json.dumps(payload, ensure_ascii=False)
    )


def call_openai(api_key: str, base_url: str, model: str, prompt: str, max_tokens: int) -> SummaryResult:
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是专业新闻编辑。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
        },
        timeout=40,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    highlights, summary = parse_llm_output(content)
    return SummaryResult(highlights=highlights, summary=summary)


def call_kimi(api_key: str, base_url: str, model: str, prompt: str, max_tokens: int) -> SummaryResult:
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是专业新闻编辑。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
        },
        timeout=40,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    highlights, summary = parse_llm_output(content)
    return SummaryResult(highlights=highlights, summary=summary)


def call_glm(api_key: str, base_url: str, model: str, prompt: str, max_tokens: int) -> SummaryResult:
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是专业新闻编辑。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
        },
        timeout=40,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    highlights, summary = parse_llm_output(content)
    return SummaryResult(highlights=highlights, summary=summary)


def parse_llm_output(content: str) -> tuple[list[str], str]:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    highlights: list[str] = []
    summary_lines: list[str] = []
    section = None
    for line in lines:
        if line.lower().startswith("highlights") or line.startswith("重点"):
            section = "highlights"
            continue
        if line.lower().startswith("summary") or line.startswith("摘要"):
            section = "summary"
            continue
        if section == "summary":
            summary_lines.append(line.lstrip("- "))
        else:
            highlights.append(line.lstrip("- "))
    if not summary_lines:
        summary_lines = [line for line in lines[-3:]]
    return highlights, "\n".join(summary_lines)


def summarize_articles(
    articles: Iterable[Article],
    provider: str,
    model: str,
    max_tokens: int,
    highlight_count: int,
    llm_config: dict[str, dict[str, str]],
) -> SummaryResult:
    prompt = build_prompt(articles, highlight_count)
    provider_config = llm_config.get(provider, {})
    api_key = provider_config.get("api_key")
    base_url = provider_config.get("base_url")
    if not api_key or not base_url:
        return default_summary(articles, highlight_count)

    if provider == "openai":
        return call_openai(api_key, base_url, model, prompt, max_tokens)
    if provider == "kimi":
        return call_kimi(api_key, base_url, model, prompt, max_tokens)
    if provider == "glm":
        return call_glm(api_key, base_url, model, prompt, max_tokens)

    return default_summary(articles, highlight_count)
