from fixlens.safety import detect_hazards

def test_swollen_battery_is_flagged():
    assert "Possible swollen or bulging battery" in detect_hazards("My phone has a swollen battery")

def test_smoke_is_flagged():
    assert "Smoke, flame, or burning smell" in detect_hazards("There is smoke from the charger")

def test_normal_symptom_has_no_hazard():
    assert detect_hazards("The screen is cracked but the phone is cool") == []

def test_empty_input_is_safe():
    assert detect_hazards("") == []
