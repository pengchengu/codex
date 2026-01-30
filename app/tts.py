from __future__ import annotations

from pathlib import Path

import requests


def generate_tts_openai(
    text: str,
    api_key: str,
    base_url: str,
    voice: str,
    audio_format: str,
    output_path: Path,
) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.post(
        f"{base_url}/audio/speech",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "gpt-4o-mini-tts",
            "voice": voice,
            "input": text,
            "format": audio_format,
        },
        timeout=60,
    )
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return str(output_path)


def generate_tts_local(text: str, output_path: Path, voice: str) -> str | None:
    try:
        import pyttsx3
    except ModuleNotFoundError:
        return None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    engine = pyttsx3.init()
    if voice:
        for candidate in engine.getProperty("voices"):
            if voice.lower() in candidate.name.lower():
                engine.setProperty("voice", candidate.id)
                break
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()
    return str(output_path)
