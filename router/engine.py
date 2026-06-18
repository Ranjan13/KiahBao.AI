import os
import logging
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KiahBaoEngine:
    """
    Connects the LlamaIndex query settings to the local 27B Gemma-SEA-LION-v4-IT model.
    Optimized for low-latency local execution on Apple Silicon.
    """
    def __init__(self, model_name: str = "kiahbao-ai"):
        self.model_name = model_name
        self.llm = self._init_llm()

    def _init_llm(self) -> Ollama:
        logging.info(f"Initializing connection to local LLM '{self.model_name}' served via Ollama...")
        try:
            # We configure a generous timeout of 120s since 27B is a substantial model
            llm = Ollama(model=self.model_name, request_timeout=120.0)
            
            # Apply to global LlamaIndex Settings
            Settings.llm = llm
            logging.info("LlamaIndex settings updated successfully.")
            return llm
        except Exception as e:
            logging.error(f"Failed to hook up local Ollama instance: {e}")
            raise e

if __name__ == "__main__":
    # Test instance connection
    try:
        engine = KiahBaoEngine()
        print("Successfully initiated engine model configurations!")
    except Exception:
        print("Note: Ensure Ollama is running and the model is built.")
