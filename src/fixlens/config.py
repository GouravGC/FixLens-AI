import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    provider: str = os.getenv("FIXLENS_PROVIDER", "ollama").strip().lower()
    model: str = os.getenv("FIXLENS_MODEL", "llama3.2-vision")
    ollama_host: str = os.getenv(
        "OLLAMA_HOST", "http://localhost:11434"
    ).rstrip("/")
    timeout_seconds: int = int(
        os.getenv("FIXLENS_TIMEOUT_SECONDS",
                  os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
    )
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    openrouter_model: str = os.getenv(
        "OPENROUTER_MODEL", "meta-llama/llama-4-scout:free"
    )
    openrouter_base_url: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    ).rstrip("/")


settings = Settings()