import os
import requests
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Target folders
BASE_DIR = Path(__file__).resolve().parent.parent
CPF_DIR = BASE_DIR / "data" / "raw" / "cpf_policies"
HDB_DIR = BASE_DIR / "data" / "raw" / "hdb_regulations"

# Ensure directories exist
CPF_DIR.mkdir(parents=True, exist_ok=True)
HDB_DIR.mkdir(parents=True, exist_ok=True)

# List of official/public PDFs for Singapore housing policies
DOWNLOADS = [
    # ── CPF Housing & Ownership Guidelines ──
    {
        "url": "https://www.cpf.gov.sg/content/dam/web/member/home-ownership/documents/buying-a-home-with-cpf-infographic.pdf",
        "filename": "buying_a_home_with_cpf.pdf",
        "target_dir": CPF_DIR,
        "description": "CPF Home Ownership Guidelines Infographic"
    },
    # ── HDB Core Guides ──
    {
        "url": "https://www.hdb.gov.sg/cs/infoweb/doc/buying-a-flat-brochure.pdf",
        "filename": "buying_a_flat_brochure.pdf",
        "target_dir": HDB_DIR,
        "description": "Official HDB Buying a Flat Brochure"
    },
    {
        "url": "https://www.hdb.gov.sg/cs/infoweb/doc/living-in-an-hdb-flat-brochure.pdf",
        "filename": "living_in_an_hdb_flat.pdf",
        "target_dir": HDB_DIR,
        "description": "HDB Flat Owner Living and Community Guidelines"
    }
]

def download_file(url: str, filepath: Path, desc: str):
    """Downloads a single file from url and saves it to filepath."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    logging.info(f"Downloading: {desc}...")
    logging.info(f"URL: {url}")
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        
        # If the official server is hosting behind a firewall/CDN and blocks, handle cleanly
        if response.status_code == 404:
            logging.warning(f"⚠️ Document not found (404) at the source link. Skipping.")
            return False
        response.raise_for_status()

        # Write to file
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logging.info(f"✓ Successfully saved to: {filepath.name} ({filepath.stat().st_size:,} bytes)\n")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to download {desc}: {e}\n")
        return False

def main():
    print("==================================================")
    print("      KiahBao.AI — Document Downloader 🏡         ")
    print("==================================================")
    print("This script fetches public CPF & HDB guides directly into your raw data directories.\n")

    success_count = 0
    for idx, item in enumerate(DOWNLOADS, 1):
        dest_path = item["target_dir"] / item["filename"]
        print(f"[{idx}/{len(DOWNLOADS)}] {item['description']}")
        
        # Skip download if already exists
        if dest_path.exists() and dest_path.stat().st_size > 1024:
            print(f"ℹ File already exists and is not empty: {dest_path.name}. Skipping.\n")
            success_count += 1
            continue

        if download_file(item["url"], dest_path, item["description"]):
            success_count += 1

    print("==================================================")
    print(f"📊 Download Completed! ({success_count}/{len(DOWNLOADS)} documents ready)")
    print("==================================================")
    print("💡 Next Step: Run 'python ingestion/pdf_splitter.py' to parse the PDFs for RAG!")

if __name__ == "__main__":
    main()
