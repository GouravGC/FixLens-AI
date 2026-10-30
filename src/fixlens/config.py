
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Provider
    provider: str = os.getenv(
        "FIXLENS_PROVIDER", "baseten"
    ).strip().lower()

    # Baseten / Meta Muse Spark Open
    baseten_api_key: str = os.getenv(
        "BASETEN_API_KEY", ""
    ).strip()

    baseten_base_url: str = os.getenv(
        "BASETEN_BASE_URL",
        "https://inference.baseten.co/v1",
    ).rstrip("/")

    baseten_model: str = os.getenv(
        "BASETEN_MODEL",
        "meta-models/muse-spark-open",
    ).strip()

    # Backward compatibility with existing tests and modules
    @property
    def model(self) -> str:
        """Return the configured model identifier."""
        return self.baseten_model

    # Pricing in USD per million tokens
    baseten_input_price: float = 1.25
    baseten_cached_input_price: float = 0.15
    baseten_output_price: float = 4.25

    # Inference settings
    timeout_seconds: int = int(
        os.getenv("FIXLENS_TIMEOUT_SECONDS", "180")
    )

    max_output_tokens: int = max(
        2000,
        int(os.getenv("FIXLENS_MAX_OUTPUT_TOKENS", "2000")),
    )

    # Retrieval settings
    top_k: int = int(
        os.getenv("FIXLENS_TOP_K", "3")
    )

    chunk_size: int = int(
        os.getenv("FIXLENS_CHUNK_SIZE", "500")
    )

    chunk_overlap: int = int(
        os.getenv("FIXLENS_CHUNK_OVERLAP", "50")
    )

    # Video and image settings
    video_max_frames: int = int(
        os.getenv("FIXLENS_VIDEO_MAX_FRAMES", "2")
    )

    image_max_width: int = int(
        os.getenv("FIXLENS_IMAGE_MAX_WIDTH", "768")
    )


settings = Settings()
