from typing import List
from core.parser import parse_document
from core.embbeding import run_pipeline
from core.embbeding import file_exists
from utils.output_answers import transform_answers

import logging


def evaluate_logic(document: str, questions: List[str]):
    
    id, context= parse_document(document)

    if not context:
        raise ValueError("Document parsing failed: context is empty.")
    try:
        pipeline_results = run_pipeline(
            doc_id=ids,
            text=context,
            questions=questions,
            meta={"source": "policy.pdf"}
        )
        
        output = transform_answers(pipeline_results)
        return output
        # print(pipeline_results)

    except Exception as e:
        logging.error(f"[ERROR] Q&A Testing failed: {e}")

   
