from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass
class PushProvider:
    type: str
    name: str
    url: str


def push_webhook(provider: PushProvider, payload: dict) -> None:
    if not provider.url:
        return
    response = requests.post(provider.url, json=payload, timeout=20)
    response.raise_for_status()


def push_feishu(provider: PushProvider, payload: dict) -> None:
    if not provider.url:
        return
    text_lines = payload.get("highlights", [])
    summary = payload.get("summary", "")
    text = "\n".join(text_lines + ([summary] if summary else []))
    body = {
        "msg_type": "text",
        "content": {"text": f"{payload.get('title', '晨报')}\n{text}"},
    }
    response = requests.post(provider.url, json=body, timeout=20)
    response.raise_for_status()


def push_wecom(provider: PushProvider, payload: dict) -> None:
    if not provider.url:
        return
    text_lines = payload.get("highlights", [])
    summary = payload.get("summary", "")
    text = "\n".join(text_lines + ([summary] if summary else []))
    body = {
        "msgtype": "text",
        "text": {"content": f"{payload.get('title', '晨报')}\n{text}"},
    }
    response = requests.post(provider.url, json=body, timeout=20)
    response.raise_for_status()


def push_update(providers: list[PushProvider], payload: dict) -> None:
    for provider in providers:
        if provider.type == "webhook":
            push_webhook(provider, payload)
        if provider.type == "feishu":
            push_feishu(provider, payload)
        if provider.type == "wecom":
            push_wecom(provider, payload)
