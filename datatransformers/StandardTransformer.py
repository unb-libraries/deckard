from sentence_transformers import SentenceTransformer

class StandardTransformer:
    def __init__(self, model, log):
        self.log = log
        log.info(f"Loading Sentence Transformer Model: {model}")
        self.transformer = SentenceTransformer(
            model,
            device='cuda'
        )

    def get(self):
        return self.transformer
