
import streamlit as st

from fixlens.config import settings
from fixlens.diagnosis import diagnose
from fixlens.safety import detect_hazards
from fixlens.video import extract_video_frames


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="FixLens AI",
    page_icon="🔧",
    layout="wide",
)

st.title("🔧 FixLens AI")
st.caption(
    "AI-assisted device troubleshooting using image and video evidence."
)


# --------------------------------------------------
# Baseten configuration
# --------------------------------------------------

with st.sidebar:
    st.header("Configuration")

    st.markdown("### Baseten — Muse Spark Open")
    st.write(f"**Model:** `{settings.baseten_model}`")
    st.write(f"**Endpoint:** `{settings.baseten_base_url}`")

    if settings.baseten_api_key:
        st.success("Baseten API key configured")
    else:
        st.error("BASETEN_API_KEY is missing.")

    st.divider()

    st.subheader("Inference limits")
    st.write(f"**Maximum output tokens:** {settings.max_output_tokens}")
    st.write(f"**Maximum video frames:** {settings.video_max_frames}")
    st.write(f"**Maximum image width:** {settings.image_max_width}px")


st.divider()


# --------------------------------------------------
# User inputs
# --------------------------------------------------

left, right = st.columns(2)

with left:
    st.subheader("1. Describe the problem")

    device = st.text_input(
        "Device or equipment",
        placeholder="e.g. laptop, washing machine, router",
    )

    symptoms = st.text_area(
        "Symptoms",
        placeholder=(
            "Describe the issue, warning lights, sounds, "
            "or error messages."
        ),
        height=150,
    )

    uploaded_photo = st.file_uploader(
        "Upload a photo (optional)",
        type=["png", "jpg", "jpeg", "webp"],
        key="fixlens_photo",
    )

    uploaded_video = st.file_uploader(
        "Upload a video (optional)",
        type=["mp4", "mov", "avi", "mkv"],
        key="fixlens_video",
    )


# --------------------------------------------------
# Evidence preview
# --------------------------------------------------

with right:
    st.subheader("2. Review evidence")

    image_bytes = None
    frames = []

    if uploaded_photo is not None:
        image_bytes = uploaded_photo.getvalue()

        st.image(
            image_bytes,
            caption="Uploaded photo",
            use_container_width=True,
        )

    if uploaded_video is not None:
        st.video(uploaded_video)
        st.caption("Video frames will be extracted for AI analysis.")

    if uploaded_photo is None and uploaded_video is None:
        st.info("Upload a photo or video to provide visual evidence.")


# --------------------------------------------------
# Diagnosis
# --------------------------------------------------

if st.button(
    "🔍 Diagnose problem",
    type="primary",
    use_container_width=True,
):

    if not settings.baseten_api_key:
        st.error(
            "BASETEN_API_KEY is missing. "
            "Add it to your .env file and restart Streamlit."
        )

    elif not device.strip():
        st.error("Please enter the device or equipment.")

    elif not symptoms.strip():
        st.error("Please describe the symptoms.")

    elif uploaded_photo is None and uploaded_video is None:
        st.error("Please upload a photo or video.")

    else:
        try:
            # Extract video frames using configured limits.
            if uploaded_video is not None:
                with st.spinner("Extracting video frames..."):
                    frames = extract_video_frames(
                        uploaded_video.getvalue(),
                        uploaded_video.name,
                        max_frames=settings.video_max_frames,
                        max_width=settings.image_max_width,
                    )

                if not frames:
                    st.error("No usable frames could be extracted.")
                    st.stop()

                st.success(f"Extracted {len(frames)} video frame(s).")

            # Safety screening
            # Keep this compatible with the existing safety module.
            if image_bytes:
                st.subheader("Safety screening")

                try:
                    hazards = detect_hazards(image_bytes)

                    if hazards:
                        st.warning("Potential safety hazards detected.")
                        st.write(hazards)
                    else:
                        st.info(
                            "No hazards were reported by the safety "
                            "screening step. This does not guarantee safety."
                        )

                except Exception as safety_error:
                    st.warning(
                        f"Safety screening could not complete: {safety_error}"
                    )

            # Call Baseten only.
            with st.spinner(
                "Analyzing evidence with Meta Muse Spark Open..."
            ):
                result = diagnose(
                    device=device.strip(),
                    symptoms=symptoms.strip(),
                    image_bytes=image_bytes,
                    provider="baseten",
                    image_frames=frames,
                )

            # --------------------------------------------------
            # Diagnosis report
            # --------------------------------------------------

            st.divider()
            st.subheader("🧠 Diagnosis report")

            # Supports both dictionary and string return formats.
            if isinstance(result, dict):
                report = result.get("report", "")
            else:
                report = str(result)

            if report:
                st.markdown(report)
            else:
                st.warning("The model returned an empty diagnosis.")

            # --------------------------------------------------
            # Usage and cost
            # --------------------------------------------------

            if isinstance(result, dict):
                st.divider()
                st.subheader("Inference details")

                details_left, details_right = st.columns(2)

                with details_left:
                    st.write(
                        "**Provider:**",
                        result.get("provider", "Baseten"),
                    )
                    st.write(
                        "**Model:**",
                        result.get("model", settings.baseten_model),
                    )
                    st.write(
                        "**Images analyzed:**",
                        result.get("images_analyzed", 0),
                    )
                    st.write(
                        "**Duration:**",
                        result.get("duration_seconds", "N/A"),
                    )

                usage = result.get("usage", {})

                with details_right:
                    if usage:
                        st.write(
                            "**Input tokens:**",
                            usage.get("prompt_tokens", "N/A"),
                        )
                        st.write(
                            "**Output tokens:**",
                            usage.get("completion_tokens", "N/A"),
                        )
                        st.write(
                            "**Total tokens:**",
                            usage.get("total_tokens", "N/A"),
                        )

                        estimated_cost = usage.get("estimated_cost_usd")

                        if estimated_cost is not None:
                            st.write(
                                "**Estimated cost:**",
                                f"${estimated_cost:.6f} USD",
                            )
                    else:
                        st.info(
                            "Token usage was not returned by the provider."
                        )

            # --------------------------------------------------
            # Download report
            # --------------------------------------------------

            st.download_button(
                "📥 Download diagnosis report",
                data=report,
                file_name="fixlens_diagnosis.txt",
                mime="text/plain",
                use_container_width=True,
            )

        except Exception as exc:
            st.error("Diagnosis failed.")
            st.exception(exc)

            st.info(
                "Check the Baseten API key, model ID, endpoint, "
                "and provider response."
            )
