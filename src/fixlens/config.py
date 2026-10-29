import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    provider: str = os.getenv("FIXLENS_PROVIDER", "ollama")
    model: str = os.getenv("FIXLENS_MODEL", "llama3.2-vision")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    timeout_seconds: int = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))

settings = Settings()
