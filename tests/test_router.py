import pytest
from router.dual_router import KiahBaoRouter

@pytest.fixture
def router():
    return KiahBaoRouter(mappings_path="prompt_templates/singlish_mapping.json")

def test_singlish_translation(router):
    """Verifies that colloquial terms map correctly to formal policy terms"""
    prompt = "Can I get some grant if I buy near parent block within 4km?"
    translated = router.translate_singlish(prompt)
    
    assert "Proximity Housing Grant (PHG)" in translated
    assert "EHG" not in translated  # Should not trigger unrelated mappings

def test_route_vector_intent(router):
    """Verifies purely policy-driven questions route to the vector engine"""
    res = router.route_query("Is there a rule on hacking structural wall in HDB?")
    assert res["route"] == "vector"

def test_route_api_intent(router):
    """Verifies market price queries route to the API engine"""
    res = router.route_query("what is the transacted price for a flat in yishun?")
    assert res["route"] == "api"

def test_route_hybrid_intent(router):
    """Verifies compound questions route to hybrid query layers"""
    res = router.route_query("if I get first time grant, how much does the block resale price scale?")
    assert res["route"] == "hybrid"
