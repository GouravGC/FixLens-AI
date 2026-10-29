# FixLens AI

**Visual Repair Intelligence** — a local-first prototype for turning device photos and symptom descriptions into a structured, safety-aware troubleshooting report.

## Current scope

- Streamlit user interface
- Local Ollama inference adapter
- Image + symptom prompt support
- Deterministic safety keyword checks
- Automated tests and GitHub Actions CI
- Provider configuration separated from diagnosis workflow

## Model choice

The initial local development model is `llama3.2-vision`. It accepts image and text inputs and is available through Ollama. Hardware performance depends on quantization, context, available VRAM and other running applications.

Muse Spark Open is a separate later integration: the current Ollama listing offers `muse-spark-open:cloud`; it is not a practical local download for a 12 GB GPU. The final hackathon demo should use a supported hosted Meta open-weight model if access/credits are available.

## Windows quick start

1. Install Ollama for Windows from https://ollama.com/download
2. In CMD, download the model:

   ```bat
   ollama pull llama3.2-vision
   ```

3. Start Ollama (the Windows app normally runs the local service). Check:

   ```bat
   ollama list
   ollama run llama3.2-vision
   ```

   At the model prompt, type `hello`, then exit with `/bye`.

4. Create and activate a Conda environment:

   ```bat
   conda create -n fixlens python=3.11.10 -y
   conda activate fixlens
   cd /d "PATH\TO\FixLens-AI"
   pip install -r requirements.txt
   copy .env.example .env
   ```

5. Run the app:

   ```bat
   set PYTHONPATH=%CD%\src
   streamlit run app.py
   ```

6. Run tests in another terminal from the project folder:

   ```bat
   set PYTHONPATH=%CD%\src
   pytest -q
   ```

## Configuration

Set `FIXLENS_PROVIDER`, `FIXLENS_MODEL`, `OLLAMA_HOST`, and `OLLAMA_TIMEOUT_SECONDS` in `.env`. Hosted provider adapters will be implemented later without changing the UI contract.

## Safety and limitations

This is a prototype, not professional repair advice. Visual inference can be wrong. Safety checks are intentionally conservative and keyword-based; they are not a complete hazard detector. Never handle swollen lithium batteries, exposed live wiring, or damaged mains-powered equipment based on AI advice.

## Roadmap

1. Local UI + Ollama inference
2. Structured output schema and improved safety evaluation
3. Benchmark dataset, latency/error telemetry and regression tests
4. Hosted Meta open-weight model integration through an eligible provider
5. Docker, deployment, demo evidence and submission checks
