import requests
import pandas as pd
import logging
from pathlib import Path
from typing import Optional
from verification.rule_bounds import HDB_TOWN_ALIASES

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MarketDataFetcher:
    """
    Fetches real-time HDB Resale Flat Prices from data.gov.sg
    """
    # Dataset ID for HDB Resale Flat Prices on Data.gov.sg
    # We will use the CKAN Datastore Search API pattern
    API_URL = "https://data.gov.sg/api/action/datastore_search"
    RESOURCE_ID = "f1765b54-a209-4718-8d38-a39237f502b3" 

    def __init__(self, output_dir: str = "../data/raw/market_transactions"):
        self.output_dir = Path(__file__).resolve().parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_recent_transactions(self, limit: int = 100) -> pd.DataFrame:
        """Fetches the most recent HDB resale transactions."""
        logging.info(f"Fetching {limit} recent transactions from data.gov.sg...")
        
        params = {
            "resource_id": self.RESOURCE_ID,
            "limit": limit,
            "sort": "month desc"
        }
        
        try:
            response = requests.get(self.API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            records = data.get("result", {}).get("records", [])
            df = pd.DataFrame(records)
            
            if not df.empty:
                logging.info(f"Successfully fetched {len(df)} records.")
            else:
                logging.warning("No records fetched.")
                
            return df
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data: {e}")
            return pd.DataFrame()

    @staticmethod
    def resolve_town_alias(raw_name: str) -> Optional[str]:
        """
        Resolves a user-supplied town name (e.g. 'AMK', 'ang mo kio', 'Tampines')
        to the canonical HDB town name used in the data.gov.sg dataset.
        Returns None if no match found.
        """
        key = raw_name.strip().upper()
        return HDB_TOWN_ALIASES.get(key)

    def fetch_by_town(self, town: str, limit: int = 50) -> dict:
        """
        Fetches recent HDB resale transactions filtered by town.
        Returns a summary dict with avg price, min, max, sample count, flat type breakdown,
        and the raw transaction records.
        """
        canonical_town = self.resolve_town_alias(town)
        if not canonical_town:
            return {
                "status": "unknown_town",
                "query": town,
                "message": f"Sorry lah, I don't recognise '{town}' as an HDB town. "
                           f"Try using the full name e.g. @Ang Mo Kio or @Tampines!",
                "transactions": [],
            }

        logging.info(f"Fetching transactions for town: {canonical_town}")
        params = {
            "resource_id": self.RESOURCE_ID,
            "limit": limit,
            "sort": "month desc",
            "filters": f'{{"town": "{canonical_town}"}}',
        }
        try:
            response = requests.get(self.API_URL, params=params, timeout=10)
            response.raise_for_status()
            records = response.json().get("result", {}).get("records", [])
            df = pd.DataFrame(records)

            if df.empty:
                return {
                    "status": "no_data",
                    "query": canonical_town,
                    "message": f"No recent transactions found for {canonical_town}.",
                    "transactions": [],
                }

            df["resale_price"] = pd.to_numeric(df["resale_price"], errors="coerce")
            df_valid = df.dropna(subset=["resale_price"])

            # Flat-type breakdown
            flat_type_avg = (
                df_valid.groupby("flat_type")["resale_price"]
                .mean()
                .round(0)
                .astype(int)
                .to_dict()
            )

            return {
                "status": "ok",
                "query": canonical_town,
                "average_price": round(df_valid["resale_price"].mean(), 2),
                "min_price": int(df_valid["resale_price"].min()),
                "max_price": int(df_valid["resale_price"].max()),
                "sample_count": len(df_valid),
                "by_flat_type": flat_type_avg,
                "transactions": df_valid.head(10).to_dict(orient="records"),
            }
        except Exception as e:
            logging.error(f"Error fetching data for {canonical_town}: {e}")
            return {
                "status": "error",
                "query": canonical_town,
                "message": str(e),
                "transactions": [],
            }

    def save_to_csv(self, df: pd.DataFrame, filename: str = "recent_transactions.csv"):
        """Saves the dataframe to the raw data directory."""
        if df.empty:
            logging.warning("DataFrame is empty, skipping save.")
            return False
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)
        logging.info(f"Saved transactions to {output_path}")
        return True

if __name__ == "__main__":
    fetcher = MarketDataFetcher()
    df = fetcher.fetch_recent_transactions(limit=50)
    fetcher.save_to_csv(df)
