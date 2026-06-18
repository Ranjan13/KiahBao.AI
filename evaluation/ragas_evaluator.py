import os
import logging
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FaithfulnessEvaluator:
    """
    Evaluates the RAG pipeline to ensure the LLM's outputs are strictly 
    grounded in the retrieved statutory chunks without hallucination.
    Target Faithfulness Score: > 98%
    """
    def __init__(self):
        # Requires OPENAI_API_KEY for Ragas evaluation judge
        if not os.getenv("OPENAI_API_KEY"):
            logging.warning("OPENAI_API_KEY is not set. Ragas evaluation may fail.")
            
    def run_evaluation(self, eval_data: dict) -> float:
        """
        eval_data expects lists for: 
        'question', 'answer', 'contexts', 'ground_truth'
        """
        dataset = Dataset.from_dict(eval_data)
        
        logging.info("Starting Ragas Faithfulness evaluation...")
        # We focus purely on faithfulness (no hallucination)
        result = evaluate(
            dataset,
            metrics=[faithfulness]
        )
        
        score = result.get('faithfulness', 0.0)
        logging.info(f"Faithfulness Score: {score * 100:.2f}%")
        
        if score < 0.98:
            logging.warning("Faithfulness score is below the 98% target threshold!")
            
        return score

if __name__ == "__main__":
    # Mock data structure required by Ragas
    mock_data = {
        "question": ["What is the maximum EHG grant for a family?"],
        "answer": ["The maximum Enhanced CPF Housing Grant for a family is $120,000."],
        "contexts": [["The EHG offers up to $120,000 for first-time buyer families subject to an income ceiling of $9,000."]],
        "ground_truth": ["Families can get up to $120,000 under EHG."]
    }
    
    evaluator = FaithfulnessEvaluator()
    # evaluator.run_evaluation(mock_data) # Uncomment to run
