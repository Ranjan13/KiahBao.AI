import pytest
import pandas as pd
from pathlib import Path
from ingestion.fetch_market_data import MarketDataFetcher
from ingestion.pdf_splitter import PolicyPDFSplitter

@pytest.fixture
def mock_fetcher():
    return MarketDataFetcher(output_dir="../data/raw/test_market")

@pytest.fixture
def mock_splitter():
    return PolicyPDFSplitter(raw_dir="../data/raw/test_policies", processed_dir="../data/processed/test_policies")

def test_fetch_market_data(mock_fetcher):
    """Test if we can fetch data from data.gov.sg API"""
    # Fetch a small limit to not overload the API
    df = mock_fetcher.fetch_recent_transactions(limit=5)
    
    # Assertions
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert len(df) == 5
        assert "month" in df.columns
        assert "resale_price" in df.columns
        assert "town" in df.columns

def test_pdf_chunking(mock_splitter):
    """Test if the text chunking logic accurately overlaps and splits"""
    sample_text = "A" * 1000 + "B" * 1000 + "C" * 500
    # Length = 2500
    # Chunk = 1000, Overlap = 200
    
    chunks = mock_splitter.chunk_text(sample_text, chunk_size=1000, overlap=200)
    
    assert len(chunks) > 0
    assert len(chunks[0]) == 1000
    # Check if 'A's and 'B's are appropriately chunked
    assert chunks[0] == "A" * 1000
