from __future__ import annotations

import base64
import time
import requests
from .config import settings

SYSTEM_PROMPT = """You are FixLens AI, a cautious device troubleshooting assistant.
Provide repair TRIAGE, not a definitive diagnosis. Distinguish:
1) Visible observations from the image,
2) User-reported symptoms,
3) Possible causes (ranked, with uncertainty),
4) Safe checks the user can perform without opening dangerous equipment,
5) Tools or professional help that may be needed,
6) When to stop and seek a qualified technician.
Do not claim that unseen damage is confirmed. Do not instruct users to open swollen batteries,
work on live electrical equipment, bypass safety mechanisms, or perform hazardous repairs.
If the evidence is insufficient, ask targeted follow-up questions. Keep the report concise and actionable."""

def diagnose(device: str, symptoms: str, image_bytes: bytes | None = None) -> str:
    prompt = f"""Device category: {device}
User-reported symptoms: {symptoms}

Return a Markdown report with these headings:
## Visible evidence
## Possible causes (ranked, uncertain)
## Safe next checks
## Tools / professional help
## Safety and stop conditions
## Follow-up questions

If no image was supplied, say visual evidence is unavailable."""
    message = {"role": "user", "content": prompt}
    if image_bytes:
        message["images"] = [base64.b64encode(image_bytes).decode("ascii")]

    payload = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            message,
        ],
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 700},
    }
    started = time.perf_counter()
    response = requests.post(
        f"{settings.ollama_host}/api/chat",
        json=payload,
        timeout=settings.timeout_seconds,
    )
    response.raise_for_status()
    body = response.json()
    content = body.get("message", {}).get("content", "").strip()
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    if not content:
        raise RuntimeError("The model returned an empty response.")
    return f"{content}\n\n---\n*Provider: Ollama · Model: {settings.model} · Elapsed: {elapsed_ms} ms*"
