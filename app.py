import streamlit as st
from PIL import Image
from io import BytesIO
from fixlens.config import settings
from fixlens.diagnosis import diagnose
from fixlens.safety import detect_hazards

st.set_page_config(page_title="FixLens AI", page_icon="🔎", layout="wide")

st.title("🔎 FixLens AI")
st.caption("Visual repair triage • Local-first prototype • Powered by a configurable model provider")

with st.sidebar:
    st.subheader("Runtime")
    st.write(f"Provider: **{settings.provider}**")
    st.write(f"Model: `{settings.model}`")
    st.write(f"Ollama endpoint: `{settings.ollama_host}`")
    st.caption("Local mode sends prompts/images to your local Ollama service. Hosted providers will be added in a later phase.")

left, right = st.columns([1, 1])
with left:
    st.subheader("1. Describe the problem")
    device = st.selectbox("Device category", ["Smartphone", "Laptop", "Tablet", "Headphones", "Household appliance", "Other"])
    symptoms = st.text_area("Symptoms", placeholder="Example: The phone fell, the screen has a crack, and touch input sometimes stops working.")
    uploaded = st.file_uploader("Upload a photo (optional)", type=["png", "jpg", "jpeg", "webp"])
    if uploaded:
        try:
            image = Image.open(uploaded).convert("RGB")
            st.image(image, caption="Uploaded image", use_container_width=True)
        except Exception:
            image = None
            st.error("That image could not be opened. Please upload a valid PNG, JPG or WEBP image.")
    else:
        image = None

with right:
    st.subheader("2. Get a triage report")
    st.info("This prototype provides troubleshooting suggestions, not a confirmed diagnosis or a substitute for a qualified technician.")
    if st.button("Analyze device", type="primary", use_container_width=True):
        if not symptoms.strip() and image is None:
            st.warning("Add symptoms or upload a photo first.")
        else:
            hazards = detect_hazards(symptoms)
            if hazards:
                st.error("Potential safety hazard detected")
                for hazard in hazards:
                    st.write(f"- {hazard}")
                st.warning("Stop using or charging the device if unsafe. Do not open a swollen battery or damaged mains-powered equipment. Seek qualified assistance.")
            with st.spinner("Analyzing with the configured model..."):
                try:
                    report = diagnose(
                        device=device,
                        symptoms=symptoms.strip() or "No symptom description supplied. Inspect only what is visible.",
                        image_bytes=uploaded.getvalue() if uploaded else None,
                    )
                    st.markdown(report)
                except Exception as exc:
                    st.error("Inference failed. Check that Ollama is running and the model is available.")
                    st.code(str(exc))
                    st.caption("You can still work on the UI and safety tests while inference is unavailable.")
