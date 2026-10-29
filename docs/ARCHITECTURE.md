# Architecture

Streamlit UI -> diagnosis service -> provider adapter -> Ollama local HTTP API.

Safety keyword screening runs independently of model output. The initial version does not persist user images. Later provider adapters should implement the same `diagnose` contract and normalize timeouts/errors without leaking credentials or image contents into logs.
