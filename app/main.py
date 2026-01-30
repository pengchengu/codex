from __future__ import annotations

from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import load_config
from app.push import PushProvider, push_update
from app.sources import Source, fetch_sources
from app.storage import Article, init_db, latest_brief, list_articles, save_brief, upsert_articles
from app.summarize import summarize_articles
from app.tts import generate_tts_local, generate_tts_openai


BASE_DIR = Path(__file__).resolve().parents[1]
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))


app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/data", StaticFiles(directory=str(BASE_DIR / "data")), name="data")

scheduler = BackgroundScheduler()


def build_sources(config: dict) -> list[Source]:
    sources = []
    for item in config.get("sources", []):
        sources.append(
            Source(
                id=item["id"],
                name=item["name"],
                type=item.get("type", "rss"),
                url=item["url"],
            )
        )
    return sources


def run_crawl(config: dict) -> list[Article]:
    crawl_config = config["crawl"]
    sources = build_sources(config)
    articles = fetch_sources(
        sources,
        crawl_config["user_agent"],
        crawl_config.get("proxy") or None,
        crawl_config["max_items_per_source"],
    )
    upsert_articles(articles)
    return articles


def run_summary(config: dict) -> dict:
    summary_config = config["summary"]
    articles = [
        Article(
            source_id=row["source_id"],
            title=row["title"],
            url=row["url"],
            published_at=row["published_at"],
            summary=row["summary"],
        )
        for row in list_articles(200)
    ]
    result = summarize_articles(
        articles,
        summary_config["provider"],
        summary_config["model"],
        summary_config["max_tokens"],
        summary_config["highlight_count"],
        config.get("llm", {}),
    )
    highlights_text = "\n".join(f"- {item}" for item in result.highlights)
    save_brief(highlights_text, result.summary, None)
    return {
        "highlights": result.highlights,
        "summary": result.summary,
    }


def run_tts(config: dict, summary_text: str) -> str | None:
    speech = config.get("speech", {})
    provider = speech.get("provider")
    output_dir = Path(speech.get("output_dir", "data/tts"))
    filename = datetime.utcnow().strftime("brief-%Y%m%d-%H%M%S") + "." + speech.get(
        "format", "mp3"
    )
    output_path = BASE_DIR / output_dir / filename
    if provider == "openai":
        openai_cfg = config.get("llm", {}).get("openai", {})
        if not openai_cfg.get("api_key"):
            return None
        return generate_tts_openai(
            summary_text,
            openai_cfg["api_key"],
            openai_cfg["base_url"],
            speech.get("voice", "alloy"),
            speech.get("format", "mp3"),
            output_path,
        )
    if provider == "local":
        return generate_tts_local(summary_text, output_path, speech.get("voice", ""))
    return None


def run_push(config: dict, payload: dict) -> None:
    push_config = config.get("push", {})
    if not push_config.get("enabled"):
        return
    providers = [
        PushProvider(**provider) for provider in push_config.get("providers", [])
    ]
    push_update(providers, payload)


def scheduled_digest() -> None:
    config = load_config()
    run_crawl(config)
    result = run_summary(config)
    tts_path = run_tts(config, result["summary"])
    if tts_path:
        save_brief("\n".join(result["highlights"]), result["summary"], tts_path)
    run_push(
        config,
        {
            "title": "Morning Brief",
            "highlights": result["highlights"],
            "summary": result["summary"],
            "tts": tts_path,
        },
    )


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    config = load_config()
    scheduler.add_job(
        scheduled_digest,
        "interval",
        minutes=config["crawl"]["interval_minutes"],
        id="crawl-job",
        replace_existing=True,
    )
    scheduler.start()


@app.on_event("shutdown")
def shutdown_event() -> None:
    scheduler.shutdown(wait=False)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    config = load_config()
    articles = list_articles(50)
    brief = latest_brief()
    return TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": config,
            "articles": articles,
            "brief": brief,
        },
    )


@app.post("/api/crawl")
def api_crawl() -> dict:
    config = load_config()
    articles = run_crawl(config)
    return {"inserted": len(articles)}


@app.post("/api/summary")
def api_summary() -> dict:
    config = load_config()
    result = run_summary(config)
    return result


@app.post("/api/push")
def api_push() -> dict:
    config = load_config()
    brief = latest_brief()
    if not brief:
        return {"status": "no brief"}
    payload = {
        "title": "Morning Brief",
        "highlights": brief["highlights"].splitlines(),
        "summary": brief["summary"],
        "tts": brief["tts_path"],
    }
    run_push(config, payload)
    return {"status": "sent"}


@app.post("/api/tts")
def api_tts() -> dict:
    config = load_config()
    brief = latest_brief()
    if not brief:
        return {"status": "no brief"}
    tts_path = run_tts(config, brief["summary"])
    if tts_path:
        save_brief(brief["highlights"], brief["summary"], tts_path)
    return {"status": "ok", "tts": tts_path}
