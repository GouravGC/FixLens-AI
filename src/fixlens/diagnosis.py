from __future__ import annotations

import base64
import time
from typing import Any

import requests

from fixlens.config import settings


SYSTEM_PROMPT = """
You are FixLens AI, an expert device troubleshooting assistant.

Analyze the user's device description and visual evidence.

Rules:
- Separate directly observed evidence from possible causes.
- Never claim an unverified component has failed.
- Give up to three plausible causes.
- Recommend practical, safe troubleshooting steps.
- Never advise touching live electrical components.
- Never recommend powering on a liquid-damaged device.
- Recommend professional inspection when necessary.
- Clearly identify uncertainty and missing evidence.

Return a concise report using exactly these sections:

## 1. Observed evidence
## 2. Possible causes
## 3. Recommended checks
## 4. Safety precautions
## 5. When to contact a technician

Keep the complete report around 150-250 words.
Do not output internal reasoning. Only return the final report.
"""


def _image_mime_type(image_bytes: bytes) -> str:
    """Identify common image formats."""

    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"

    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    return "image/jpeg"


def _image_content(image_bytes: bytes) -> dict[str, Any]:
    """Convert image bytes into an API-compatible image block."""

    encoded = base64.b64encode(image_bytes).decode("ascii")
    mime_type = _image_mime_type(image_bytes)

    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{mime_type};base64,{encoded}",
            "detail": "low",
        },
    }


def _build_user_content(
    prompt: str,
    image_bytes: bytes | None,
    image_frames: list[tuple[float, bytes]] | None,
) -> list[dict[str, Any]]:
    """Build multimodal content from text, photos and video frames."""

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": prompt,
        }
    ]

    if image_bytes:
        content.append({
            "type": "text",
            "text": "Uploaded device photograph:",
        })

        content.append(_image_content(image_bytes))

    for index, (timestamp, frame_bytes) in enumerate(
        image_frames or [],
        start=1,
    ):
        content.append({
            "type": "text",
            "text": (
                f"Video frame {index}, "
                f"timestamp {float(timestamp):.2f} seconds:"
            ),
        })

        content.append(_image_content(frame_bytes))

    return content


def _extract_report(data: dict[str, Any]) -> str:
    """Extract the final user-facing response."""

    choices = data.get("choices") or []

    if not choices:
        raise RuntimeError(
            "Baseten returned no completion choices. "
            f"Response: {str(data)[:2000]}"
        )

    choice = choices[0]
    message = choice.get("message") or {}
    content = message.get("content")

    if isinstance(content, str):
        report = content.strip()

    elif isinstance(content, list):
        text_parts = [
            str(item["text"])
            for item in content
            if isinstance(item, dict) and item.get("text")
        ]

        report = "\n".join(text_parts).strip()

    else:
        report = ""

    if not report:
        finish_reason = choice.get("finish_reason")
        usage = data.get("usage") or {}

        if finish_reason == "length":
            raise RuntimeError(
                "Muse Spark reached its output-token limit before "
                "finishing the diagnosis. "
                f"finish_reason={finish_reason!r}; "
                f"usage={usage}. "
                "Try reducing the number of visual inputs."
            )

        raise RuntimeError(
            "Muse Spark returned an empty final answer. "
            f"finish_reason={finish_reason!r}; "
            f"usage={usage}"
        )

    return report


def _calculate_baseten_cost(
    usage: dict[str, Any],
) -> dict[str, Any]:
    """Estimate the cost of one inference request."""

    prompt_tokens = int(
        usage.get("prompt_tokens", 0) or 0
    )

    completion_tokens = int(
        usage.get("completion_tokens", 0) or 0
    )

    total_tokens = int(
        usage.get(
            "total_tokens",
            prompt_tokens + completion_tokens,
        ) or 0
    )

    details = (
        usage.get("prompt_tokens_details")
        or usage.get("input_tokens_details")
        or {}
    )

    cached_tokens = int(
        details.get("cached_tokens", 0) or 0
    )

    cached_tokens = max(
        0,
        min(cached_tokens, prompt_tokens),
    )

    regular_input_tokens = prompt_tokens - cached_tokens

    input_cost = (
        regular_input_tokens * settings.baseten_input_price
        + cached_tokens * settings.baseten_cached_input_price
    ) / 1_000_000

    output_cost = (
        completion_tokens * settings.baseten_output_price
    ) / 1_000_000

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cached_tokens": cached_tokens,
        "input_cost_usd": round(input_cost, 8),
        "output_cost_usd": round(output_cost, 8),
        "estimated_cost_usd": round(
            input_cost + output_cost,
            8,
        ),
    }


def _baseten_inference(
    prompt: str,
    image_bytes: bytes | None = None,
    image_frames: list[tuple[float, bytes]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Send a multimodal diagnosis request to Baseten."""

    if not settings.baseten_api_key:
        raise RuntimeError(
            "BASETEN_API_KEY is missing. "
            "Configure it in your .env file."
        )

    endpoint = (
        f"{settings.baseten_base_url.rstrip('/')}/chat/completions"
    )

    user_content = _build_user_content(
        prompt=prompt,
        image_bytes=image_bytes,
        image_frames=image_frames,
    )

    payload = {
        "model": settings.baseten_model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        "temperature": 0.2,
        "max_tokens": settings.max_output_tokens,
        "reasoning_effort": "low",
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {settings.baseten_api_key}",
        "Content-Type": "application/json",
    }

    started = time.perf_counter()

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=settings.timeout_seconds,
        )

    except requests.Timeout as exc:
        raise RuntimeError(
            "Baseten request timed out. "
            "Increase FIXLENS_TIMEOUT_SECONDS or retry."
        ) from exc

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not connect to Baseten: {exc}"
        ) from exc

    duration = time.perf_counter() - started

    if not response.ok:
        raise RuntimeError(
            f"Baseten API returned HTTP {response.status_code}: "
            f"{response.text[:2500]}"
        )

    try:
        data = response.json()

    except ValueError as exc:
        raise RuntimeError(
            "Baseten returned an invalid JSON response: "
            f"{response.text[:2000]}"
        ) from exc

    report = _extract_report(data)

    usage = data.get("usage") or {}
    usage_details = _calculate_baseten_cost(usage)

    metadata = {
        "provider": "Baseten",
        "model": settings.baseten_model,
        "duration_seconds": round(duration, 3),
        "images_analyzed": (
            int(bool(image_bytes)) + len(image_frames or [])
        ),
        "usage": usage_details,
        "finish_reason": (
            (data.get("choices") or [{}])[0].get("finish_reason")
        ),
    }

    return report, metadata


def diagnose(
    device: str,
    symptoms: str,
    image_bytes: bytes | None = None,
    provider: str = "baseten",
    image_frames: list[tuple[float, bytes]] | None = None,
) -> dict[str, Any]:
    """Run a device diagnosis using Baseten Muse Spark Open."""

    if provider.strip().lower() != "baseten":
        raise ValueError(
            "This FixLens build supports Baseten only."
        )

    if not device.strip():
        raise ValueError("Device name cannot be empty.")

    if not symptoms.strip():
        raise ValueError("Symptoms cannot be empty.")

    if not image_bytes and not image_frames:
        raise ValueError(
            "Upload a photograph or provide at least one video frame."
        )

    prompt = f"""
Diagnose this device using the supplied visual evidence.

DEVICE:
{device.strip()}

REPORTED SYMPTOMS:
{symptoms.strip()}

Analyze all supplied photographs and video frames.
Return the five-section troubleshooting report.
Keep the report concise, safe and evidence-based.
"""

    report, metadata = _baseten_inference(
        prompt=prompt,
        image_bytes=image_bytes,
        image_frames=image_frames,
    )

    return {
        "report": report,
        **metadata,
    }