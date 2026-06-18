import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

CPF_POLICY_TEXT = """--- CHUNK 1 ---
CPF HOUSING USE RULES & ELIGIBILITY FOR HDB FLATS
Singaporeans can use savings in their CPF Ordinary Account (CPF-OA) to purchase a Housing & Development Board (HDB) flat.

1. Ordinary Account Usage Limits:
- For BTO flats, buyers can use CPF-OA up to the purchase price or valuation, whichever is lower.
- For resale flats, the maximum amount of CPF-OA that can be used is capped at the Valuation Limit (VL). The VL is the purchase price or the valuation of the flat at the time of purchase, whichever is lower.
- The Withdraw Limit (WL) is 120% of the Valuation Limit. Once the WL is reached, no further CPF-OA savings can be withdrawn for the flat.

2. Lease Cover Rule (Age + Remaining Lease):
- To utilize the maximum eligible CPF-OA for housing, the remaining lease of the flat must cover the youngest buyer to at least the age of 95.
- If the remaining lease does not cover the youngest buyer to age 95, the amount of CPF-OA that can be used will be pro-rated.
- No CPF-OA can be used at all if the remaining lease of the flat is less than 20 years.

--- CHUNK 2 ---
CPF HOUSING GRANTS & FAMILY HOUSING SCHEME
Eligible first-timer buyers can receive CPF housing grants to assist with their flat purchase.

1. Enhanced CPF Housing Grant (EHG):
- Eligible for both BTO and resale HDB flats.
- Income ceiling: Household monthly income must not exceed $9,000 for families, or $4,500 for singles.
- The youngest buyer must be employed continuously for at least 12 months before the flat application and still be employed.
- Maximum EHG grant for families is $120,000, and $60,000 for singles. The grant amount is tiered based on household income.

2. CPF Housing Grant (for Resale Flats only):
- First-timer families buying a 2-room to 4-room resale flat can get up to $80,000.
- First-timer families buying a 5-room or larger resale flat can get up to $50,000.
- Citizenship requirement: At least one buyer must be a Singapore Citizen (SC). If one buyer is SC and the other is a Permanent Resident (PR), they qualify for the SC-PR family grant (capped at $40,000). Two PRs qualify for the PR-PR grant of $20,000.
"""

HDB_POLICY_TEXT = """--- CHUNK 1 ---
HDB RENOVATION GUIDELINES & STRUCTURAL SAFETY
To ensure the structural integrity and safety of HDB blocks, flat owners must strictly adhere to HDB's renovation guidelines.

1. Permit Requirements:
- Any demolition, hacking, or alteration of walls (whether load-bearing or non-load-bearing) requires an official HDB Renovation Permit.
- Hacking or tampering with reinforced concrete (RC) columns, structural beams, or load-bearing shear walls is strictly prohibited. Doing so is a serious structural offense and will result in heavy fines and mandatory restoration costs.
- Owners must hire an HDB Registered Renovation Contractor (HBDRC) to carry out any renovation works.

2. Ceiling and Floor Finishes:
- The thickness of floor screed and finishes must not exceed 50mm to prevent overloading the floor slabs.
- Drilling or structural hacking on the ceiling is prohibited if it compromises structural integrity or damages the floor slabs of the unit above.

--- CHUNK 2 ---
HDB MINIMUM OCCUPATION PERIOD (MOP) & RESALE RULES
Every HDB flat owner is subject to the Minimum Occupation Period (MOP) guidelines.

1. Minimum Occupation Period (MOP):
- The standard MOP for standard BTO and resale HDB flats is 5 years.
- During the MOP, owners are not allowed to sell the flat, rent out the entire flat, or invest in private residential property.
- For flats purchased under Prime Location Housing (PLH) or Plus flat categories, the MOP is 10 years.
- The MOP is calculated from the date of key collection. Any period of non-occupation (e.g., living overseas) does not count towards the MOP.

2. Resale HDB Flat Eligibility:
- Singapore Citizens (SC) can buy any new or resale flat.
- Permanent Residents (PR) can only buy resale flats. They must have held PR status for at least 3 years before they are eligible to purchase a resale flat.
- Singles are eligible to buy 2-room BTO flats or any size resale flat under the Single Singapore Citizen Scheme once they turn 35.
"""

def main():
    print("==================================================")
    print("  KiahBao.AI — Local Policy Data Builder 🏡       ")
    print("==================================================")
    print("Writing core CPF & HDB housing rules directly into the RAG directory...\n")

    cpf_file = PROCESSED_DIR / "cpf_policies_processed.txt"
    hdb_file = PROCESSED_DIR / "hdb_regulations_processed.txt"

    try:
        with open(cpf_file, "w", encoding="utf-8") as f:
            f.write(CPF_POLICY_TEXT.strip())
        logging.info(f"✓ Saved CPF RAG rules to: {cpf_file.name}")

        with open(hdb_file, "w", encoding="utf-8") as f:
            f.write(HDB_POLICY_TEXT.strip())
        logging.info(f"✓ Saved HDB RAG rules to: {hdb_file.name}")

        print("\n==================================================")
        print("🎉 Policy Data Setup Successful!")
        print("==================================================")
        print("💡 The RAG system now has complete local policy documents!")
        print("   KiahBao.AI will now automatically read these rules for RAG queries.")
    except Exception as e:
        logging.error(f"❌ Failed to write files: {e}")

if __name__ == "__main__":
    main()
