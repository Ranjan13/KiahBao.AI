import os
import logging
from pathlib import Path
from PyPDF2 import PdfReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PolicyPDFSplitter:
    """
    Parses and splits dense HDB/CPF policy PDFs into text chunks 
    optimized for LlamaIndex vector ingestion.
    """
    def __init__(self, raw_dir: str = "../data/raw", processed_dir: str = "../data/processed"):
        base_path = Path(__file__).resolve().parent
        self.raw_dir = base_path / raw_dir
        self.processed_dir = base_path / processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def extract_text(self, pdf_path: str) -> str:
        """Extracts all text from a given PDF."""
        try:
            reader = PdfReader(pdf_path)
            full_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    full_text.append(text)
            return "\n".join(full_text)
        except Exception as e:
            logging.error(f"Failed to read PDF {pdf_path}: {e}")
            return ""

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """
        Splits text into chunks by character count with overlap.
        In a production setting, LlamaIndex's SentenceSplitter is preferred, 
        but this serves as our raw data processor.
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
            
        return chunks

    def process_all_pdfs(self, sub_folder: str = "cpf_policies"):
        """Iterates over raw PDFs and outputs processed text chunks."""
        target_dir = self.raw_dir / sub_folder
        if not target_dir.exists():
            logging.warning(f"Directory {target_dir} does not exist.")
            return

        pdf_files = list(target_dir.glob("*.pdf"))
        logging.info(f"Found {len(pdf_files)} PDFs in {sub_folder}.")

        for pdf_file in pdf_files:
            logging.info(f"Processing {pdf_file.name}...")
            text = self.extract_text(str(pdf_file))
            if not text:
                continue
                
            chunks = self.chunk_text(text)
            
            # Save processed chunks to a text file
            output_file = self.processed_dir / f"{pdf_file.stem}_processed.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, chunk in enumerate(chunks):
                    f.write(f"--- CHUNK {i+1} ---\n{chunk}\n\n")
            
            logging.info(f"Saved {len(chunks)} chunks to {output_file}")

if __name__ == "__main__":
    splitter = PolicyPDFSplitter()
    # Mock run, assuming user places PDF in data/raw/cpf_policies
    splitter.process_all_pdfs("cpf_policies")
    splitter.process_all_pdfs("hdb_regulations")
