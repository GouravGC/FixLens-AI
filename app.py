
from io import BytesIO

import streamlit as st
from PIL import Image

from fixlens.config import settings
from fixlens.diagnosis import diagnose
from fixlens.safety import detect_hazards
from fixlens.video import extract_video_frames


st.set_page_config(
    page_title="FixLens AI",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 FixLens AI")
st.caption("Visual repair triage • Local and hosted inference")


# -------------------- Sidebar --------------------

with st.sidebar:
    st.subheader("Inference settings")

    providers = {
        "Ollama (Local)": "ollama",
        "OpenRouter (Hosted)": "openrouter",
    }

    default_provider = (
        "openrouter"
        if str(settings.provider).lower() == "openrouter"
        else "ollama"
    )
    default_label = next(
        label for label, value in providers.items()
        if value == default_provider
    )

    selected_label = st.radio(
        "Select inference provider",
        options=list(providers.keys()),
        index=list(providers.keys()).index(default_label),
        key="fixlens_provider_radio_v2",
    )

    provider = providers[selected_label]

    if provider == "ollama":
        st.markdown("### Ollama (Local)")
        st.write(f"**Model:** `{settings.model}`")
        st.write(f"**Endpoint:** `{settings.ollama_host}`")
        st.info("Inference runs locally through Ollama.")
    else:
        st.markdown("### OpenRouter (Hosted)")
        st.write(f"**Model:** `{settings.openrouter_model}`")
        st.write("**Endpoint:** `https://openrouter.ai/api/v1`")

        if settings.openrouter_api_key:
            st.success("API key configured")
        else:
            st.error("OPENROUTER_API_KEY is missing.")

        st.info("Uploaded visual evidence is sent to the hosted provider.")


# -------------------- Input --------------------

input_col, report_col = st.columns([1, 1])

with input_col:
    st.subheader("1. Describe the problem")

    device = st.selectbox(
        "Device category",
        [
            "Smartphone",
            "Laptop",
            "Tablet",
            "Headphones",
            "Household appliance",
            "Other",
        ],
    )

    symptoms = st.text_area(
        "Symptoms",
        placeholder="Describe the issue, error messages, damage, or unusual behavior.",
        height=130,
    )

    uploaded = st.file_uploader(
        "Upload device photo or video",
        type=["png", "jpg", "jpeg", "webp", "mp4", "mov", "avi"],
        accept_multiple_files=False,
        help="Images and videos up to Streamlit's configured upload limit.",
        key="fixlens_evidence_v2",
    )

    image_bytes = None
    video_bytes = None
    upload_kind = None

    if uploaded is not None:
        filename = uploaded.name.lower()

        if filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
            upload_kind = "image"
            try:
                image = Image.open(BytesIO(uploaded.getvalue())).convert("RGB")
                image.thumbnail((2048, 2048))

                st.image(
                    image,
                    caption="Uploaded device photo",
                    use_container_width=True,
                )

                buffer = BytesIO()
                image.save(buffer, format="JPEG", quality=90)
                image_bytes = buffer.getvalue()
            except Exception as exc:
                st.error(f"Could not read the image: {exc}")

        elif filename.endswith((".mp4", ".mov", ".avi")):
            upload_kind = "video"
            video_bytes = uploaded.getvalue()
            if video_bytes:
                st.video(video_bytes)
            else:
                st.error("The video file is empty.")


# -------------------- Analysis --------------------

with report_col:
    st.subheader("2. Repair triage report")

    st.warning(
        "Safety first: this tool offers preliminary troubleshooting, "
        "not a confirmed diagnosis. Do not open swollen batteries or "
        "work on live electrical equipment."
    )

    if st.button("Analyze device", type="primary", use_container_width=True):
        if uploaded is None:
            st.error("Upload a device photo or video first.")
        elif not symptoms.strip():
            st.error("Enter the device symptoms first.")
        elif upload_kind == "image" and image_bytes is None:
            st.error("The image could not be processed.")
        elif upload_kind == "video" and not video_bytes:
            st.error("The video could not be read.")
        elif upload_kind not in ("image", "video"):
            st.error("Upload a supported photo or video.")
        elif provider == "openrouter" and not settings.openrouter_api_key:
            st.error(
                "OpenRouter API key is missing. Configure OPENROUTER_API_KEY "
                "in your environment and restart Streamlit."
            )
        else:
            # Safety screening
            try:
                hazards = detect_hazards(symptoms.strip())
            except Exception as exc:
                hazards = None
                st.error(f"Safety screening failed: {exc}")

            if hazards is None:
                st.warning("Analysis stopped because safety screening failed.")
            else:
                if isinstance(hazards, bool):
                    hazard_found = hazards
                    hazard_messages = ["Potential hazard detected."]
                elif isinstance(hazards, str):
                    hazard_found = bool(hazards.strip())
                    hazard_messages = [hazards] if hazard_found else []
                else:
                    hazard_messages = list(hazards) if hazards else []
                    hazard_found = bool(hazard_messages)

                if hazard_found:
                    st.error("Potential safety hazard detected.")
                    for item in hazard_messages:
                        st.write(f"- {item}")

                    st.warning(
                        "Stop using the device if it appears unsafe. "
                        "Disconnect power only if it is safe to do so, "
                        "and seek qualified professional assistance."
                    )
                else:
                    try:
                        frames = None

                        if upload_kind == "video":
                            with st.spinner("Extracting representative video frames..."):
                                frames = extract_video_frames(
                                    video_bytes,
                                    filename=uploaded.name,
                                    max_frames=4,
                                    max_width=1024,
                                )

                            st.success(f"Extracted {len(frames)} frames.")

                            with st.expander("Preview analyzed frames"):
                                for timestamp, frame_data in frames:
                                    st.image(
                                        frame_data,
                                        caption=f"Approx. {timestamp:.2f} seconds",
                                        use_container_width=True,
                                    )

                        with st.spinner(f"Analyzing with {selected_label}..."):
                            report = diagnose(
                                device=device,
                                symptoms=symptoms.strip(),
                                image_bytes=image_bytes if upload_kind == "image" else None,
                                provider=provider,
                                image_frames=frames,
                            )

                        st.success("Analysis complete")
                        st.markdown(report)

                        st.download_button(
                            "Download report",
                            data=report,
                            file_name="fixlens_diagnostic_report.md",
                            mime="text/markdown",
                            use_container_width=True,
                        )

                    except Exception as exc:
                        st.error("Analysis failed.")
                        st.code(str(exc))
                        st.caption(
                            "Check your provider credentials, model support, "
                            "Ollama status, network connection, and video format."
                        )


st.divider()
st.caption(
    "FixLens AI • Prototype for repair triage. Model outputs may be inaccurate; "
    "verify any repair decision with a qualified technician."
)
