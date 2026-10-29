# Model integration plan

## Local development
- Ollama model: `llama3.2-vision:11b`
- Local endpoint: `http://localhost:11434/api/chat`
- Image bytes are base64 encoded for the Ollama API request.

## Later hosted inference
Implement one adapter per provider after confirming its current endpoint, model identifier, image format, credit eligibility and terms. Do not assume Ollama's cloud model is free or that a provider credit covers every deployment charge.
