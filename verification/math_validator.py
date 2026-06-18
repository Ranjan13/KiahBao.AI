import re
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from verification.rule_bounds import (
    MAX_EHG_FAMILY, MAX_EHG_SINGLE,
    INCOME_CEILING_EHG_FAMILY, INCOME_CEILING_EHG_SINGLE,
    MAX_PHG_FAMILY_LIVING_WITH, MAX_PHG_FAMILY_LIVING_NEAR,
    MAX_PHG_SINGLE_LIVING_WITH, MAX_PHG_SINGLE_LIVING_NEAR,
    MAX_CPF_GRANT_SC_PR_FAMILY, MAX_CPF_GRANT_PR_PR_FAMILY,
    INCOME_CEILING_CPF_GRANT_FAMILY,
    TARGET_AGE
)


class BuyerProfile(BaseModel):
    """
    Represents the parameters of the HDB buyer profile.
    Supports both Singapore Citizens (SC) and Permanent Residents (PR).
    """
    youngest_buyer_age: int = Field(..., ge=21, le=120)
    flat_remaining_lease: int = Field(..., ge=1, le=99)
    average_monthly_income: float = Field(..., ge=0)
    is_family: bool = True
    proximity_km: Optional[float] = None
    living_with_parents: bool = False

    # ── PR-specific fields ──────────────────────────────────────────────────
    citizenship_status: Literal["SC", "PR"] = Field(
        default="SC",
        description="SC = Singapore Citizen | PR = Permanent Resident"
    )
    partner_citizenship: Literal["SC", "PR", "none"] = Field(
        default="none",
        description="Citizenship of spouse/partner. 'none' if single."
    )
    has_parents_in_sg: bool = Field(
        default=True,
        description="Whether buyer's parents are Singapore-based (required for PHG)."
    )
    years_as_pr: Optional[int] = Field(
        default=3,
        description="Number of years held PR status."
    )


class GrantCalculator:
    """
    Deterministically computes CPF Housing Grants based on statutory bounds.
    Handles both SC and PR buyer profiles correctly.
    """

    @staticmethod
    def is_sc_applicant(profile: BuyerProfile) -> bool:
        """Returns True if at least one applicant is a Singapore Citizen."""
        return (
            profile.citizenship_status == "SC"
            or profile.partner_citizenship == "SC"
        )

    @staticmethod
    def calculate_lease_proration(age: int, lease: int) -> float:
        """
        Calculates lease proration factor.
        If the remaining lease covers the youngest buyer to age 95, factor is 1.0.
        Otherwise, it is pro-rated down.
        """
        coverage_age = age + lease
        if coverage_age >= TARGET_AGE:
            return 1.0
        factor = lease / (TARGET_AGE - age)
        return min(max(factor, 0.0), 1.0)

    @staticmethod
    def calculate_ehg(profile: BuyerProfile) -> float:
        """
        Calculates Enhanced CPF Housing Grant (EHG) eligibility.
        EHG is ONLY available to Singapore Citizens.
        """
        # Hard gate — PRs (with no SC partner) are ineligible
        if not GrantCalculator.is_sc_applicant(profile):
            return 0.0

        ceiling = INCOME_CEILING_EHG_FAMILY if profile.is_family else INCOME_CEILING_EHG_SINGLE
        if profile.average_monthly_income > ceiling:
            return 0.0

        base_max = MAX_EHG_FAMILY if profile.is_family else MAX_EHG_SINGLE
        step_income = 500 if profile.is_family else 250
        step_grant = 5000 if profile.is_family else 2500

        tiers_over_min = int(profile.average_monthly_income // step_income)
        calculated_base = max(base_max - (tiers_over_min * step_grant), 0.0)

        proration_factor = GrantCalculator.calculate_lease_proration(
            profile.youngest_buyer_age, profile.flat_remaining_lease
        )
        return calculated_base * proration_factor

    @staticmethod
    def calculate_phg(profile: BuyerProfile) -> float:
        """
        Calculates Proximity Housing Grant (PHG) eligibility.
        PHG requires:
          - At least one SC applicant
          - Parents must be Singapore-based
          - Living within 4km of parents
        """
        # Hard gate — PHG requires SC + parents in SG
        if not GrantCalculator.is_sc_applicant(profile):
            return 0.0
        if not profile.has_parents_in_sg:
            return 0.0
        if profile.proximity_km is None or profile.proximity_km > 4.0:
            return 0.0

        if profile.is_family:
            return MAX_PHG_FAMILY_LIVING_WITH if profile.living_with_parents else MAX_PHG_FAMILY_LIVING_NEAR
        else:
            return MAX_PHG_SINGLE_LIVING_WITH if profile.living_with_parents else MAX_PHG_SINGLE_LIVING_NEAR

    @staticmethod
    def calculate_cpf_housing_grant_pr(profile: BuyerProfile) -> float:
        """
        Calculates CPF Housing Grant for PR applicants buying resale flats.
        This replaces EHG for mixed SC+PR couples and two-PR households.
        Income ceiling: $14,000/month combined.
        Note: PRs can only buy RESALE flats (not BTO/SBF).
        """
        # Only applies when at least one applicant is PR
        if profile.citizenship_status == "SC" and profile.partner_citizenship in ("SC", "none"):
            return 0.0  # Pure SC buyers use EHG instead

        if profile.average_monthly_income > INCOME_CEILING_CPF_GRANT_FAMILY:
            return 0.0

        # SC + PR couple
        if GrantCalculator.is_sc_applicant(profile) and profile.is_family:
            return MAX_CPF_GRANT_SC_PR_FAMILY

        # Two PRs
        if profile.citizenship_status == "PR" and profile.partner_citizenship == "PR":
            return MAX_CPF_GRANT_PR_PR_FAMILY

        return 0.0

    @staticmethod
    def get_grant_summary(profile: BuyerProfile) -> dict:
        """
        Returns a full grant eligibility summary for a buyer profile.
        Automatically selects the correct grant scheme (SC vs PR path).
        """
        is_sc = GrantCalculator.is_sc_applicant(profile)
        has_pr_component = (
            profile.citizenship_status == "PR"
            or profile.partner_citizenship == "PR"
        )

        if is_sc and not has_pr_component:
            # Pure SC — EHG + PHG path
            ehg = GrantCalculator.calculate_ehg(profile)
            phg = GrantCalculator.calculate_phg(profile)
            return {
                "scheme": "SC (EHG + PHG)",
                "ehg": ehg,
                "phg": phg,
                "cpf_housing_grant": 0.0,
                "total": ehg + phg,
                "notes": [],
            }
        elif is_sc and has_pr_component:
            # SC + PR couple — CPF Housing Grant (resale only), no EHG, no PHG
            cpf_grant = GrantCalculator.calculate_cpf_housing_grant_pr(profile)
            notes = [
                "SC+PR couples are NOT eligible for EHG or PHG.",
                "CPF Housing Grant applies to RESALE flats only (not BTO).",
            ]
            if not profile.has_parents_in_sg:
                notes.append("PHG not applicable — parents are not Singapore-based.")
            return {
                "scheme": "SC+PR (CPF Housing Grant)",
                "ehg": 0.0,
                "phg": 0.0,
                "cpf_housing_grant": cpf_grant,
                "total": cpf_grant,
                "notes": notes,
            }
        else:
            # Two PRs — limited CPF Housing Grant, resale only
            cpf_grant = GrantCalculator.calculate_cpf_housing_grant_pr(profile)
            pr_notes = [
                "PRs are NOT eligible for EHG or PHG.",
                "CPF Housing Grant applies to RESALE flats only.",
                "PHG not applicable — PHG is for Singapore Citizens only.",
            ]
            if profile.years_as_pr is not None and profile.years_as_pr < 3:
                pr_notes.append(f"⚠️ Ineligible: Both PR buyers must hold PR status for ≥ 3 years (currently: {profile.years_as_pr} years).")
            else:
                pr_notes.append(f"✓ PR status duration condition met (≥ 3 years).")
                
            return {
                "scheme": "PR+PR (CPF Housing Grant, Resale Only)",
                "ehg": 0.0,
                "phg": 0.0,
                "cpf_housing_grant": cpf_grant,
                "total": cpf_grant,
                "notes": pr_notes,
            }


class OutputVerification(BaseModel):
    """
    Pydantic parser to parse and intercept output validation.
    Extracts numerical grants computed by the LLM and checks them against deterministic caps.
    """
    llm_output: str
    buyer_profile: BuyerProfile

    @model_validator(mode='after')
    def verify_financial_bounds(self) -> 'OutputVerification':
        matches = re.findall(r'\$?([0-9]{1,3},[0-9]{3}|[0-9]{2,6})\b', self.llm_output)
        extracted_amounts = [int(m.replace(',', '')) for m in matches]

        summary = GrantCalculator.get_grant_summary(self.buyer_profile)
        max_total_legal = summary["total"]

        for amount in extracted_amounts:
            if amount > max_total_legal and amount > 5000:
                raise ValueError(
                    f"Hallucination Warning: LLM returned grant figure of ${amount:,}, "
                    f"but maximum statutory limit for this profile ({summary['scheme']}) "
                    f"is ${max_total_legal:,.2f}."
                )
        return self
