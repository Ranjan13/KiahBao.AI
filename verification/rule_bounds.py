# Singapore HDB Statutory Bounds and Grants Rules (Updated 2026)
# Source: HDB InfoWEB — CPF Housing Grants for Resale Flats

# ── Singapore Citizens (SC) ─────────────────────────────────────────────────

# Enhanced CPF Housing Grant (EHG) — SC only, resale & BTO
MAX_EHG_FAMILY = 120000
MAX_EHG_SINGLE = 60000

INCOME_CEILING_EHG_FAMILY = 9000
INCOME_CEILING_EHG_SINGLE = 4500

# Proximity Housing Grant (PHG) — SC only, parents/children must be in SG
MAX_PHG_FAMILY_LIVING_WITH = 30000
MAX_PHG_FAMILY_LIVING_NEAR = 20000
MAX_PHG_SINGLE_LIVING_WITH = 15000
MAX_PHG_SINGLE_LIVING_NEAR = 10000

# ── Permanent Residents (PR) ────────────────────────────────────────────────
# PRs are NOT eligible for: EHG, PHG, or Step-Up CPF Housing Grant.
# PRs can only buy RESALE flats (not BTO/SBF).
# CPF Housing Grant (Family) for resale — income ceiling $14,000/month
# SC+PR couple:
MAX_CPF_GRANT_SC_PR_FAMILY  = 40000   # CPF Family Grant (SC+PR couple)
MAX_CPF_GRANT_SC_PR_SINGLES = 20000   # CPF Singles Grant (SC+PR, not applicable jointly)
# Two PRs:
MAX_CPF_GRANT_PR_PR_FAMILY  = 20000   # CPF Family Grant (two PRs)

INCOME_CEILING_CPF_GRANT_FAMILY = 14000  # Combined income ceiling for CPF Housing Grant
PR_MINIMUM_RESIDENCY_YEARS = 3            # PRs must hold PR for ≥3 years before buying HDB

# ── Shared ──────────────────────────────────────────────────────────────────
MAX_PROXIMITY_KM = 4.0
TARGET_AGE = 95   # Lease must cover youngest buyer to age 95

# ── HDB Town Name Aliases (for @ location lookup) ───────────────────────────
# Canonical HDB towns as per data.gov.sg dataset, plus common aliases
HDB_TOWN_ALIASES: dict[str, str] = {
    # Canonical names (uppercase as in API)
    "ANG MO KIO":       "ANG MO KIO",
    "BEDOK":            "BEDOK",
    "BISHAN":           "BISHAN",
    "BUKIT BATOK":      "BUKIT BATOK",
    "BUKIT MERAH":      "BUKIT MERAH",
    "BUKIT PANJANG":    "BUKIT PANJANG",
    "BUKIT TIMAH":      "BUKIT TIMAH",
    "CENTRAL AREA":     "CENTRAL AREA",
    "CHOA CHU KANG":    "CHOA CHU KANG",
    "CLEMENTI":         "CLEMENTI",
    "GEYLANG":          "GEYLANG",
    "HOUGANG":          "HOUGANG",
    "JURONG EAST":      "JURONG EAST",
    "JURONG WEST":      "JURONG WEST",
    "KALLANG/WHAMPOA":  "KALLANG/WHAMPOA",
    "MARINE PARADE":    "MARINE PARADE",
    "PASIR RIS":        "PASIR RIS",
    "PUNGGOL":          "PUNGGOL",
    "QUEENSTOWN":       "QUEENSTOWN",
    "SEMBAWANG":        "SEMBAWANG",
    "SENGKANG":         "SENGKANG",
    "SERANGOON":        "SERANGOON",
    "TAMPINES":         "TAMPINES",
    "TOA PAYOH":        "TOA PAYOH",
    "WOODLANDS":        "WOODLANDS",
    "YISHUN":           "YISHUN",
    # Common aliases / abbreviations
    "AMK":              "ANG MO KIO",
    "CCK":              "CHOA CHU KANG",
    "KW":               "KALLANG/WHAMPOA",
    "KALLANG":          "KALLANG/WHAMPOA",
    "WHAMPOA":          "KALLANG/WHAMPOA",
    "JURONG":           "JURONG WEST",
    "JW":               "JURONG WEST",
    "JE":               "JURONG EAST",
    "BP":               "BUKIT PANJANG",
    "BB":               "BUKIT BATOK",
    "BT BATOK":         "BUKIT BATOK",
    "BT PANJANG":       "BUKIT PANJANG",
    "BT MERAH":         "BUKIT MERAH",
    "BT TIMAH":         "BUKIT TIMAH",
    "MP":               "MARINE PARADE",
    "PR":               "PASIR RIS",  # won't conflict — only matched in town lookup
    "QT":               "QUEENSTOWN",
    "SB":               "SEMBAWANG",
    "SK":               "SENGKANG",
    "TP":               "TAMPINES",
    "TOAPAYOH":         "TOA PAYOH",
    "WOODIE":           "WOODLANDS",
    "PUNGGOL NORTH":    "PUNGGOL",
    "CENTRAL":          "CENTRAL AREA",
    "CITY":             "CENTRAL AREA",
}
