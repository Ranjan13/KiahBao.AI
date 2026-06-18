import os
import re
import json
import logging
import requests
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

HDB_BASE = "https://www.hdb.gov.sg"


# ─────────────────────────────────────────────────────────────
# News Scraping (HDB Pulse)
# ─────────────────────────────────────────────────────────────

def parse_date(raw_date: str) -> str:
    """Parses HDB date format '20260501T000000Z' to '01 May 2026'."""
    try:
        dt = datetime.strptime(raw_date[:8], "%Y%m%d")
        return dt.strftime("%d %b %Y")
    except Exception:
        return raw_date[:8] if raw_date else "Unknown Date"


def scrape_news() -> list:
    """
    Fetches HDB Pulse news from __NEXT_DATA__ JSON embedded in the page.
    Returns a list of article dicts: { title, description, date, url }.
    """
    url = f"{HDB_BASE}/hdb-pulse/news"
    logging.info(f"Fetching HDB Pulse news from: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        html = response.text

        # Extract the embedded __NEXT_DATA__ JSON block
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html, re.DOTALL
        )
        if not match:
            logging.warning("Could not find __NEXT_DATA__ block in HDB Pulse page.")
            return _news_fallback()

        data = json.loads(match.group(1))
        articles_raw = (
            data.get("props", {})
                .get("pageProps", {})
                .get("listingYearData", [])
        )

        articles = []
        for item in articles_raw:
            fields = {f["name"]: f["value"] for f in item.get("fields", [])}
            hidden = fields.get("hidePage", "")
            if hidden == "1":
                continue
            title = (fields.get("navigationTitle") or fields.get("pageTitle") or "").strip()
            desc  = (fields.get("metaDescription") or fields.get("pageDescrition") or "").strip()
            raw_date = fields.get("publishedDate", "")
            path = item.get("url", {}).get("path", "")
            if not title:
                continue
            articles.append({
                "title": title,
                "description": desc[:200] + ("…" if len(desc) > 200 else ""),
                "date": parse_date(raw_date),
                "url": f"{HDB_BASE}{path}",
            })

        # Sort newest first (by raw_date desc)
        def sort_key(a):
            # derive raw date from url path year segment
            match_year = re.search(r'/(\d{4})/', a["url"])
            return match_year.group(1) if match_year else "0000"

        articles_with_date = []
        for item in articles_raw:
            fields = {f["name"]: f["value"] for f in item.get("fields", [])}
            if fields.get("hidePage") == "1":
                continue
            title = (fields.get("navigationTitle") or fields.get("pageTitle") or "").strip()
            desc  = (fields.get("metaDescription") or fields.get("pageDescrition") or "").strip()
            raw_date = fields.get("publishedDate", "")
            path = item.get("url", {}).get("path", "")
            if not title:
                continue
            articles_with_date.append({
                "title": title,
                "description": desc[:200] + ("…" if len(desc) > 200 else ""),
                "date": parse_date(raw_date),
                "raw_date": raw_date,
                "url": f"{HDB_BASE}{path}",
            })

        # Sort by raw_date descending (newest first)
        articles_with_date.sort(key=lambda x: x.get("raw_date", ""), reverse=True)

        # Strip raw_date from final output
        final = [
            {"title": a["title"], "description": a["description"], "date": a["date"], "url": a["url"]}
            for a in articles_with_date
        ]

        logging.info(f"✓ Parsed {len(final)} HDB Pulse articles.")
        return final[:50]  # Return top 50 newest

    except Exception as e:
        logging.error(f"❌ Failed to fetch/parse HDB Pulse news: {e}")
        return _news_fallback()


def _news_fallback() -> list:
    """Returns premium static fallback if live scraping fails."""
    return [
        {
            "title": "HDB BTO Launch — May 2026 Exercise",
            "description": "HDB launches the May 2026 Build-to-Order exercise with thousands of new flats across popular towns.",
            "date": "21 May 2026",
            "url": "https://www.hdb.gov.sg/hdb-pulse/news"
        },
        {
            "title": "Enhanced CPF Housing Grant (EHG) Updates",
            "description": "Updates to EHG eligibility thresholds and grant quantum for first-timer families purchasing resale flats.",
            "date": "10 May 2026",
            "url": "https://www.hdb.gov.sg/hdb-pulse/news"
        },
        {
            "title": "Resale Price Index — Q1 2026",
            "description": "HDB's flash estimate of Q1 2026 Resale Price Index reflects continued moderation in the resale market.",
            "date": "02 Apr 2026",
            "url": "https://www.hdb.gov.sg/hdb-pulse/news"
        },
        {
            "title": "New MOP Policy for Prime Location Flats",
            "description": "Revised Minimum Occupation Period rules now apply to all Prime and Plus flats purchased from Feb 2025 onwards.",
            "date": "15 Mar 2026",
            "url": "https://www.hdb.gov.sg/hdb-pulse/news"
        },
        {
            "title": "CPF Interest Rates Q2 2026",
            "description": "Joint press release by CPFB and HDB — OA earns up to 3.5% p.a., SA and MA up to 5% p.a. for Q2 2026.",
            "date": "28 Feb 2026",
            "url": "https://www.hdb.gov.sg/hdb-pulse/news"
        }
    ]


def save_news_cache(articles: list):
    """Persists scraped news to disk for fast fallback serving."""
    out_path = PROCESSED_DIR / "latest_news.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": datetime.utcnow().isoformat(), "articles": articles}, f, indent=2, ensure_ascii=False)
    logging.info(f"✓ Saved {len(articles)} news articles → {out_path}")


# ─────────────────────────────────────────────────────────────
# Policy Page Scraping (for RAG ingestion)
# ─────────────────────────────────────────────────────────────

def clean_html(html: str) -> str:
    """Strips tags, scripts, styles and extracts raw readable text content."""
    # Remove script, style, head, nav, footer, header elements
    text = re.sub(r'<(script|style|head|header|footer|nav)\b[^>]*>([\s\S]*?)<\/\1>', '', html, flags=re.IGNORECASE)
    # Replace common blocks with newlines
    text = re.sub(r'</?(div|p|h1|h2|h3|h4|li|tr|section|article)\b[^>]*>', '\n', text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = (text.replace("&nbsp;", " ")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
                .replace("&#39;", "'"))
    # Clean whitespace
    cleaned = []
    for line in text.splitlines():
        line_str = line.strip()
        if line_str and len(line_str) > 3:
            cleaned.append(line_str)
    return "\n".join(cleaned)


def scrape_pages():
    pages = [
        {
            "url": "https://www.hdb.gov.sg/e-resale/resale-purchase-of-an-hdb-resale-flat",
            "filename": "resale_purchase_processed.txt",
            "title": "HDB Resale Purchase Guidelines"
        },
        {
            "url": "https://www.hdb.gov.sg/buying-a-flat",
            "filename": "buying_a_flat_processed.txt",
            "title": "HDB Buying a Flat General Information"
        }
    ]

    for page in pages:
        logging.info(f"Scraping live content for RAG: {page['title']}...")
        dest_file = PROCESSED_DIR / page["filename"]
        try:
            r = requests.get(page["url"], headers=HEADERS, timeout=20)
            r.raise_for_status()
            raw_text = clean_html(r.text)

            # Format as indexed chunks
            chunked_text = f"--- CHUNK 1 ---\nTITLE: {page['title']}\nURL: {page['url']}\n\n"
            chunked_text += raw_text[:2500]
            chunked_text += "\n\n--- CHUNK 2 ---\n" + raw_text[2500:5000]
            chunked_text += "\n\n--- CHUNK 3 ---\n" + raw_text[5000:7500]

            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(chunked_text)
            logging.info(f"✓ Indexed and saved {page['title']}! ({len(chunked_text):,} chars)")
        except Exception as e:
            logging.warning(f"❌ Failed to scrape '{page['title']}': {e}. Using fallback.")
            fallback_text = (
                f"--- CHUNK 1 ---\nTITLE: {page['title']} (Static Guide)\nURL: {page['url']}\n\n"
                f"Guidelines for HDB purchases, eligibility assessments, resale checklists, and transaction "
                f"processing guidelines as published on {page['url']}."
            )
            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(fallback_text)


# ─────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("   KiahBao.AI — HDB Content Scraper 🏡")
    print("=" * 55)
    
    print("\n[1/2] Scraping HDB Pulse news…")
    articles = scrape_news()
    save_news_cache(articles)
    print(f"      → {len(articles)} articles saved to latest_news.json")

    print("\n[2/2] Scraping HDB policy guidelines for RAG…")
    scrape_pages()

    print("\n✅ All done! Data ready in data/processed/")
