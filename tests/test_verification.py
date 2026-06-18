import pytest
from pydantic import ValidationError
from verification.math_validator import BuyerProfile, GrantCalculator, OutputVerification

def test_lease_proration():
    """Lease covers to age 95 = 1.0, otherwise pro-rated down."""
    # covers (30 + 65 = 95) -> 1.0
    factor = GrantCalculator.calculate_lease_proration(age=30, lease=65)
    assert factor == 1.0

    # covers (30 + 50 = 80) -> pro-rated (50 / 65)
    factor_short = GrantCalculator.calculate_lease_proration(age=30, lease=50)
    assert factor_short < 1.0
    assert factor_short == 50 / 65

def test_ehg_income_ceiling():
    """If household monthly income exceeds 9000 limit, grant must be 0"""
    profile = BuyerProfile(
        youngest_buyer_age=30,
        flat_remaining_lease=70,
        average_monthly_income=9500,
        is_family=True
    )
    ehg = GrantCalculator.calculate_ehg(profile)
    assert ehg == 0.0

def test_ehg_calculation_perfect_match():
    """Test standard sliding scale maximum grant"""
    profile = BuyerProfile(
        youngest_buyer_age=30,
        flat_remaining_lease=70,  # Covers to 100 > 95
        average_monthly_income=4500, # Mid-tier family income
        is_family=True
    )
    # Household income tier: decrement = (4500 // 500) * 5000 = 45000.
    # Base = 120000 - 45000 = 75000
    ehg = GrantCalculator.calculate_ehg(profile)
    assert ehg == 75000.0

def test_hallucination_guard_intercepts():
    """Verifies Pydantic OutputVerification raises error on LLM hallucinated calculations"""
    profile = BuyerProfile(
        youngest_buyer_age=35,
        flat_remaining_lease=50, # 35 + 50 = 85 (Lease does not cover to 95!)
        average_monthly_income=3000,
        is_family=True,
        proximity_km=3.0,
        living_with_parents=False
    )
    # Target maximum EHG: (120000 - 30000) * (50/60) = 90000 * 0.833 = 75000
    # Target PHG: 20000
    # Legal Total = 95000
    
    # Correct response should succeed
    OutputVerification(
      llm_output="Based on your profile, you are eligible for $75,000 EHG and $20,000 PHG.",
      buyer_profile=profile
    )
    
    # Hallucinated response (exceeding ceiling) must raise ValidationError
    with pytest.raises(ValidationError) as excinfo:
        OutputVerification(
          llm_output="Aiyo, you got high discount! You qualify for a grant of $150,000!",
          buyer_profile=profile
        )
    assert "Hallucination Warning" in str(excinfo.value)
