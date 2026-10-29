
from __future__ import annotations

import base64
import time

import requests

from .config import settings


SYSTEM_PROMPT = """
You are FixLens AI, a cautious device troubleshooting assistant.

Provide preliminary repair triage, not a definitive diagnosis.
Separate visible evidence from user-reported symptoms and uncertain causes.
Rank possible causes and explain uncertainty.
For video frames, describe only what is visible in the supplied frames.
Do not claim to have observed motion between frames that were not analyzed.

Recommend safe, non-invasive checks only.
Never instruct users to open swollen batteries, work on live electrical
equipment, bypass safety mechanisms, or perform dangerous repairs.
Recommend qualified professional assistance when appropriate.
"""


def diagnose(
    device: str,
    symptoms: str,
    image_bytes: bytes | None = None,
    provider: str | None = None,
    image_frames: list[tuple[float, bytes]] | None = None,
) -> str:
    selected_provider = (provider or settings.provider).strip().lower()

    frames = list(image_frames or [])

    if image_bytes:
        frames = [(0.0, image_bytes)]

    if not frames:
        raise ValueError("A photo or at least one video frame is required.")

    prompt = f"""
Device category: {device}
Reported symptoms: {symptoms}

Visual evidence: {len(frames)} image frame(s).
For video, timestamps indicate the approximate position of each sampled frame.
Analyze only the supplied images. Do not infer unseen details.

Return a Markdown report using these sections:

## Visible evidence
Describe what is actually visible. If evidence is unclear, say so.

## Possible causes
List plausible causes in ranked order. State uncertainty.

## Safe next checks
Give simple, non-invasive checks only.

## Tools or professional help
Explain whether a technician or specialist may be needed.

## Safety and stop conditions
List relevant precautions and conditions requiring the user to stop.

## Follow-up questions
Ask useful questions that would narrow down the possible causes.
"""

    started = time.perf_counter()

    if selected_provider == "ollama":
        payload = {
            "model": settings.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": prompt,
                    "images": [
                        base64.b64encode(data).decode("ascii")
                        for _, data in frames
                    ],
                },
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 700,
            },
        }

        try:
            response = requests.post(
                f"{settings.ollama_host.rstrip('/')}/api/chat",
                json=payload,
                timeout=settings.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                "Could not connect to Ollama. Check that Ollama is running "
                "and the configured model is installed. "
                f"Details: {exc}"
            ) from exc

        provider_label = "Ollama (Local)"
        model_name = settings.model

    elif selected_provider == "openrouter":
        if not settings.openrouter_api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is missing. Configure it and restart the app."
            )

        content = [{"type": "text", "text": prompt}]

        for timestamp, data in frames:
            encoded = base64.b64encode(data).decode("ascii")
            content.append({
                "type": "text",
                "text": f"Sampled video frame timestamp: {timestamp:.2f} seconds.",
            })
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encoded}"
                },
            })

        payload = {
            "model": settings.openrouter_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            "temperature": 0.2,
            "max_tokens": 900,
            "stream": False,
        }

        try:
            response = requests.post(
                f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/GouravGC/FixLens-AI",
                    "X-Title": "FixLens AI",
                },
                json=payload,
                timeout=settings.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Could not connect to OpenRouter. Details: {exc}"
            ) from exc

        provider_label = "OpenRouter (Hosted)"
        model_name = settings.openrouter_model

    else:
        raise ValueError(
            f"Unsupported provider '{selected_provider}'. "
            "Choose 'ollama' or 'openrouter'."
        )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:800]
        raise RuntimeError(
            f"{provider_label} returned HTTP {response.status_code}: {detail}"
        ) from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"{provider_label} returned an invalid JSON response."
        ) from exc

    if selected_provider == "ollama":
        report = body.get("message", {}).get("content", "")
    else:
        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError(
                f"OpenRouter returned no choices: {str(body)[:500]}"
            )

        message = choices[0].get("message") or {}
        report = message.get("content", "")

        if isinstance(report, list):
            report = "\n".join(
                item.get("text", "")
                for item in report
                if isinstance(item, dict) and item.get("type") == "text"
            )

    if not isinstance(report, str) or not report.strip():
        raise RuntimeError(
            f"{provider_label} returned an empty report. "
            "Check model availability and image-input support."
        )

    elapsed_ms = round((time.perf_counter() - started) * 1000)

    return (
        f"{report.strip()}\n\n---\n"
        f"*Provider: {provider_label} · Model: {model_name} · "
        f"Images analyzed: {len(frames)} · Time: {elapsed_ms} ms*"
    )
