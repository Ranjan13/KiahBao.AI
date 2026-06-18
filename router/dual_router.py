import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KiahBaoRouter:
    """
    Context Hybrid Router (Tier 2)
    Analyzes the user's prompt (supporting colloquial Singlish/acronyms),
    maps colloquialisms to formal housing policy terms, and routes the query:
    - VECTOR: Policy searches (CPF, HDB regulations)
    - API: Real-time price inquiries (data.gov.sg transactions)
    - HYBRID: When both policy details and actual pricing are required.
    """
    def __init__(self, mappings_path: str = "prompt_templates/singlish_mapping.json"):
        base_path = Path(__file__).resolve().parent
        self.mappings_path = base_path / mappings_path
        self.mappings = self._load_mappings()

    def _load_mappings(self) -> list:
        try:
            if self.mappings_path.exists():
                with open(self.mappings_path, 'r') as f:
                    data = json.load(f)
                    return data.get("mappings", [])
            else:
                logging.warning(f"Mappings file not found at {self.mappings_path}, using empty fallback.")
                return []
        except Exception as e:
            logging.error(f"Failed to load Singlish mappings: {e}")
            return []

    def translate_singlish(self, prompt: str) -> str:
        """Translates colloquial Singaporean terms to formal policy terms in the prompt context."""
        cleaned_prompt = prompt.lower()
        translated = prompt
        
        for mapping in self.mappings:
            shorthand = mapping["shorthand"]
            if shorthand in cleaned_prompt:
                formal = mapping["formal_term"]
                logging.info(f"Singlish Match found: '{shorthand}' -> '{formal}'")
                translated += f" (Context search mapping: {formal} - {mapping['context']})"
                
        return translated

    @staticmethod
    def extract_location_mention(prompt: str) -> Optional[str]:
        """
        Detects @Location mentions in the user's prompt.
        Returns the raw location string if found, else None.
        Strips trailing Singlish particles (lah, ah, meh, lor, hor, leh) and punctuation.
        Examples: '@Tampines ah' → 'Tampines', '@Ang Mo Kio?' → 'Ang Mo Kio'
        """
        match = re.search(r'@([A-Za-z][A-Za-z\s/\-]{1,30})', prompt)
        if not match:
            return None
        raw = match.group(1).strip()
        # Strip trailing Singlish particles, filler words, and punctuation
        raw = re.sub(
            r'\s+(lah|ah|meh|lor|hor|leh|sia|bro|man|what|right|or not|'
            r'how|prices?|please|now|today|recently|got|still|any|like)\b.*$',
            '', raw, flags=re.IGNORECASE
        ).rstrip('?!.,;: ')
        return raw or None

    def route_query(self, prompt: str) -> Dict[str, Any]:
        """
        Classifies query intent dynamically.
        Returns:
            Dict containing route ('vector', 'api', 'api_location', or 'hybrid'),
            the translated prompt, and optionally a resolved 'location' key.
        """
        translated_prompt = self.translate_singlish(prompt)
        prompt_lower = prompt.lower()

        # ── Priority 1: @Location mention → skip RAG, go straight to API ──
        location_mention = self.extract_location_mention(prompt)
        if location_mention:
            logging.info(f"@Location detected: '{location_mention}' → route: API_LOCATION")
            return {
                "route": "api_location",
                "translated_prompt": translated_prompt,
                "original_prompt": prompt,
                "location": location_mention,
            }

        # ── Priority 2: Intent keyword matching ──
        needs_pricing = any(x in prompt_lower for x in [
            "price", "cost", "how much", "valuation", "transacted",
            "$", "sell for", "worth",
        ])
        
        policy_keywords = [
            "grant", "ehg", "phg", "rule", "law", "renovate", "hack",
            "demolish", "mop", "ceiling", "stay", "eligible", "pr",
            "citizen", "permanent resident",
        ]
        needs_policy = any(
            re.search(rf"\b{re.escape(x)}\b", prompt_lower) is not None
            for x in policy_keywords
        )

        if needs_pricing and needs_policy:
            route = "hybrid"
        elif needs_pricing:
            route = "api"
        else:
            route = "vector"  # Default: vector search for policy-level guidelines

        logging.info(f"Query: '{prompt}' routed to: {route.upper()}")
        return {
            "route": route,
            "translated_prompt": translated_prompt,
            "original_prompt": prompt,
            "location": None,
        }

if __name__ == "__main__":
    router = KiahBaoRouter()
    
    # Test cases
    tests = [
        "How much does a 4 room flat in Sengkang cost?",
        "Can I get grant if I stay near parent block?",
        "I want to hack structural wall of my new BTO flat. Can or not?",
        "If I get first time grant, what is the price limit for resale?"
      ]
      
    for t in tests:
        res = router.route_query(t)
        print(f"Prompt: {res['original_prompt']}\nRoute: {res['route'].upper()}\n")
