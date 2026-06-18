import pytest
from app import KiahBaoApp
from verification.math_validator import BuyerProfile

@pytest.fixture
def app():
    return KiahBaoApp()

def test_app_end_to_end_vector_route(app):
    """Test full integration loop for policy query routing and mock matching"""
    profile = BuyerProfile(
        youngest_buyer_age=30,
        flat_remaining_lease=70,
        average_monthly_income=5000,
        is_family=True
    )
    
    res = app.query("Is there any law about MOP or hacking columns in my flat?", profile)
    
    assert res["route"] == "vector"
    assert "hacking" in res["response"]
    assert "Permit" in res["response"]

def test_app_end_to_end_api_route(app):
    """Test full integration loop for transactional market routing"""
    profile = BuyerProfile(
        youngest_buyer_age=30,
        flat_remaining_lease=70,
        average_monthly_income=5000,
        is_family=True
    )
    
    res = app.query("What is the cost average for Yishun resale flat?", profile)
    
    assert res["route"] == "api"
    assert "Live HDB" in res["response"]

def test_app_end_to_end_math_safety_override(app):
    """
    Test that the orchestrator actively intercepts and overrides LLM responses 
    if they try to hallucinate impossible grant figures.
    """
    profile = BuyerProfile(
        youngest_buyer_age=35,
        flat_remaining_lease=50,  # 35 + 50 = 85 (lease does not cover to age 95!)
        average_monthly_income=3000,
        is_family=True,
        proximity_km=3.0,
        living_with_parents=False
    )
    
    # Maximum statutory EHG cap here is pro-rated: (120000 - 30000) * (50/60) = 75000
    # Maximum PHG is 20000. Total = 95000
    
    app_instance = KiahBaoApp()
    
    # We bypass LLM query and force a mock output exceeding limit to trigger verification intercept
    # Normally this happens inside query(), but we will test the override pathway directly
    test_prompt = "How much grant can get?"
    
    # Set a custom mock responses generator that breaks boundaries
    app_instance._mock_llm_response = lambda p, pr, api: "Congrats! You qualify for a grant of $150,000!"
    
    res = app_instance.query(test_prompt, profile)
    
    # The output should show the safety override warning instead of $150,000!
    assert "pricing math issue" in res["response"]
    assert "Total maximum grant" in res["response"]
    assert "$95,000" in res["response"] # Verify mathematically corrected ceiling
