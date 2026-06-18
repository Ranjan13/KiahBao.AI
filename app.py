import os
import logging
from typing import Dict, Any
from router.dual_router import KiahBaoRouter
from router.engine import KiahBaoEngine
from ingestion.fetch_market_data import MarketDataFetcher
from verification.math_validator import BuyerProfile, OutputVerification, GrantCalculator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KiahBaoApp:
    """
    KiahBao.AI Main End-to-End Orchestrator.
    Binds Ingestion (Tier 1), Router (Tier 2), Verification (Tier 3), and Evaluation (Tier 4).
    """
    def __init__(self):
        logging.info("Initializing KiahBao.AI unified core...")
        self.router = KiahBaoRouter()
        self.fetcher = MarketDataFetcher()

        try:
            self.engine = KiahBaoEngine()
        except Exception:
            logging.warning("Ollama engine offline. Running with dry-run/mock LLM fallbacks.")
            self.engine = None

    def query(self, prompt: str, profile: BuyerProfile) -> Dict[str, Any]:
        """
        Processes a user housing prompt through the full 3-Tier safety lifecycle.
        Supports routes: vector | api | hybrid | api_location
        """
        # 1. Routing & Translation (Tier 2)
        route_details = self.router.route_query(prompt)
        route = route_details["route"]
        translated_prompt = route_details["translated_prompt"]
        location = route_details.get("location")

        # ── Special fast-path: @Location price lookup ──────────────────────
        if route == "api_location":
            return self._handle_location_query(prompt, location, profile)

        # ── Standard pipeline ──────────────────────────────────────────────
        context_data = {}
        api_data_summary = ""

        # 2. Live Market API Fetching (Tier 1 - Ingestion)
        if route in ["api", "hybrid"]:
            df = self.fetcher.fetch_recent_transactions(limit=10)
            if not df.empty:
                context_data["recent_transactions"] = df.to_dict(orient="records")
                api_data_summary = f"\n[Live HDB market average transaction: ${df['resale_price'].astype(float).mean():,.2f}]"
            else:
                api_data_summary = "\n[Live HDB API reached, but no recent records found.]"

        # 3. LLM Query Execution (Tier 2 - Orchestrated with local 27B Model)
        llm_response = ""
        if self.engine and self.engine.llm:
            try:
                grant_summary = GrantCalculator.get_grant_summary(profile)
                query_str = (
                    f"Buyer Profile: {profile.model_dump_json()}\n"
                    f"Grant Scheme: {grant_summary['scheme']}\n"
                    f"User Query: {translated_prompt}\n"
                    f"API Context: {api_data_summary}"
                )
                response = self.engine.llm.complete(query_str)
                llm_response = str(response)
            except Exception as e:
                logging.error(f"Error querying Ollama model: {e}")
                llm_response = self._mock_llm_response(prompt, profile, api_data_summary)
        else:
            llm_response = self._mock_llm_response(prompt, profile, api_data_summary)

        # 4. Zero-Hallucination Math Verification (Tier 3 - Guard rails)
        verified_response = llm_response
        try:
            OutputVerification(llm_output=llm_response, buyer_profile=profile)
            logging.info("Zero-Hallucination validation check PASSED.")
        except Exception as e:
            logging.warning(f"Zero-Hallucination validation check FAILED: {e}")
            verified_response = self._build_override_response(profile, api_data_summary)
            logging.info("Override response dispatched.")

        return {
            "query": prompt,
            "route": route,
            "response": verified_response,
            "profile": profile.model_dump(),
        }

    def _handle_location_query(self, prompt: str, location: str, profile: BuyerProfile) -> Dict[str, Any]:
        """
        Fast-path handler for @Location price lookups.
        Bypasses the RAG/vector store entirely — goes straight to data.gov.sg API.
        """
        logging.info(f"Handling @location fast-path for: {location}")
        town_data = self.fetcher.fetch_by_town(location)

        if town_data["status"] == "unknown_town":
            response = town_data["message"]
        elif town_data["status"] in ("no_data", "error"):
            response = (
                f"Aiyo, I checked data.gov.sg for **{location}** but couldn't find recent transactions lah. "
                f"Maybe try the full town name? e.g. @Ang Mo Kio, @Tampines, @Woodlands."
            )
        else:
            town = town_data["query"]
            avg  = town_data["average_price"]
            lo   = town_data["min_price"]
            hi   = town_data["max_price"]
            n    = town_data["sample_count"]
            by_type = town_data.get("by_flat_type", {})

            # Format flat type breakdown
            breakdown_lines = "\n".join(
                f"  • {flat_type}: ${price:,}" for flat_type, price in sorted(by_type.items())
            )

            response = (
                f"📍 **{town} — Live HDB Resale Prices** (last {n} transactions)\n\n"
                f"💰 Average: **${avg:,.0f}**\n"
                f"📉 Lowest: ${lo:,}  |  📈 Highest: ${hi:,}\n\n"
                f"**By flat type (avg):**\n{breakdown_lines}\n\n"
                f"_Data from data.gov.sg — updated live lah!_"
            )

        return {
            "query": prompt,
            "route": "api_location",
            "response": response,
            "profile": profile.model_dump(),
        }

    def _build_override_response(self, profile: BuyerProfile, api_data_summary: str) -> str:
        """Deterministic override response when LLM grant figures fail validation."""
        summary = GrantCalculator.get_grant_summary(profile)
        scheme = summary["scheme"]
        total  = summary["total"]
        notes  = "\n".join(f"⚠️ {n}" for n in summary["notes"]) if summary["notes"] else ""

        lines = [
            "Aiyo, my system detected a pricing math issue! Let me double-check that for you lah.\n",
            f"Based on your profile **({scheme})**:\n",
        ]

        if summary["ehg"] > 0:
            lines.append(f"- **Enhanced CPF Housing Grant (EHG)**: ${summary['ehg']:,.2f}")
        if summary["phg"] > 0:
            lines.append(f"- **Proximity Housing Grant (PHG)**: ${summary['phg']:,.2f}")
        if summary["cpf_housing_grant"] > 0:
            lines.append(f"- **CPF Housing Grant**: ${summary['cpf_housing_grant']:,.2f}")
        if total == 0:
            lines.append("- ❌ **No CPF grants applicable** for this profile.")

        lines.append(f"\n**Total maximum grant: ${total:,.2f}**")
        lines.append(f"_This is strictly calculated according to HDB statutory guidelines._")

        if notes:
            lines.append(f"\n{notes}")
        if api_data_summary:
            lines.append(api_data_summary)

        return "\n".join(lines)

    def _mock_llm_response(self, prompt: str, profile: BuyerProfile, api_data_summary: str) -> str:
        """Accurate policy-aligned fallback if local model is offline."""
        prompt_lower = prompt.lower()
        summary = GrantCalculator.get_grant_summary(profile)

        if "grant" in prompt_lower or "eligible" in prompt_lower:
            return self._build_override_response(profile, api_data_summary)
        elif any(x in prompt_lower for x in ["hack", "wall", "demolish", "renovate"]):
            return (
                "For HDB structural renovation, hacking of reinforced concrete columns/walls is strictly prohibited. "
                "Any demolition works must undergo an engineering review, and you must apply for an official HDB Renovation Permit first. "
                "Don't do it blindly, very dangerous!"
            )
        elif "pr" in prompt_lower or "permanent resident" in prompt_lower:
            return (
                "Ah, for Permanent Residents (PRs), there are some key differences lah:\n\n"
                "1. PRs can ONLY buy **resale HDB flats** — no BTO or SBF access.\n"
                "2. PRs must have held PR status for **at least 3 years** before purchasing.\n"
                "3. PRs are **NOT eligible** for EHG or Proximity Housing Grant (PHG).\n"
                "4. SC+PR couples may qualify for the **CPF Housing Grant** (up to $40,000).\n"
                "5. Two-PR households may qualify for up to **$20,000** CPF Housing Grant.\n\n"
                "No need to kiah — just confirm your situation and I'll calculate the exact figures for you!"
            )
        else:
            return f"I hear you! How can I help you secure your flat safely today? {api_data_summary}"


if __name__ == "__main__":
    app = KiahBaoApp()

    profile = BuyerProfile(
        youngest_buyer_age=30,
        flat_remaining_lease=70,
        average_monthly_income=5000,
        is_family=True,
        proximity_km=2.5,
        living_with_parents=False,
        citizenship_status="SC",
        partner_citizenship="none",
        has_parents_in_sg=True,
    )

    # Test @ location query (bypasses RAG)
    res = app.query("What are the prices like @Tampines?", profile)
    print("\n--- @LOCATION QUERY ---")
    print(f"ROUTE: {res['route'].upper()}")
    print(f"RESPONSE:\n{res['response']}")

    # Test PR profile
    pr_profile = BuyerProfile(
        youngest_buyer_age=35,
        flat_remaining_lease=75,
        average_monthly_income=8000,
        is_family=True,
        proximity_km=10.0,
        living_with_parents=False,
        citizenship_status="PR",
        partner_citizenship="SC",
        has_parents_in_sg=False,
    )
    res2 = app.query("What grants can I get as a PR married to a citizen?", pr_profile)
    print("\n--- PR PROFILE QUERY ---")
    print(f"ROUTE: {res2['route'].upper()}")
    print(f"RESPONSE:\n{res2['response']}")
