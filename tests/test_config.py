from fixlens.config import settings

def test_default_provider_is_ollama():
    assert settings.provider

def test_model_is_configured():
    assert settings.model
