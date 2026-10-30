# 🔧 FixLens AI — AI-Powered Device Troubleshooting

FixLens AI is an AI-assisted device troubleshooting application that analyzes visual evidence from photographs and videos to generate structured, safety-conscious diagnostic reports.

## 🚀 Live Demo & Project Links

| Resource | Link |
|---|---|
| 🌐 Live Application | [Launch FixLens AI](https://fixlens-ai-latest.onrender.com/) |
| 🎬 Demo Video | [Watch on YouTube](https://youtu.be/V8NsoxTxZps) |
| 💻 GitHub Repository | [GouravGC/FixLens-AI](https://github.com/GouravGC/FixLens-AI) |
| ⚙️ GitHub Actions | [View CI Workflow Run](https://github.com/GouravGC/FixLens-AI/actions/runs/41055307957) |
| 🚀 Render Deployment History | [View Deployment Dashboard](https://dashboard.render.com/web/srv-dbhm7j2fngtc73c1dfog/deploys) |
| 📸 Screenshots & Evidence | [Browse Evidence Directory](evidences/) |

## 🧠 AI Model & API Integration

FixLens AI uses **Meta Muse Spark Open** through the **Baseten Model APIs** hosted inference endpoint.

- **Model:** `meta-models/muse-spark-open`
- **Model developer:** Meta
- **Inference provider:** Baseten
- **API endpoint:** `https://inference.baseten.co/v1`
- **Integration:** OpenAI-compatible chat completions API
- **Authentication:** Baseten API key supplied through environment variables

The application sends device descriptions and extracted visual evidence to the model for multimodal analysis.

The API key is stored as a deployment environment variable and is never committed to the repository.

## 🎥 Multimodal Diagnosis

- Upload device photographs for visual inspection.
- Upload videos in supported formats.
- Extract selected video frames for model analysis.
- Combine reported symptoms with visual evidence.
- Generate structured troubleshooting reports.
- Provide safety precautions and technician-referral guidance.

## ⚙️ Deployment & CI/CD

The project uses GitHub for source control and GitHub Actions for automated CI checks. The Streamlit application is deployed on Render.

- Source code and version history: GitHub
- Automated checks: GitHub Actions
- Application hosting: Render
- Model inference: Baseten Model APIs

## 📂 Project Evidence

Screenshots, application demonstrations, and supporting evidence are available in the [`evidences/`](evidences/) directory.

For a complete demonstration, watch the [FixLens AI demo video](https://youtu.be/V8NsoxTxZps) or launch the [live application](https://fixlens-ai-latest.onrender.com/).