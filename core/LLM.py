import os

from core.config import get_data_dir
from huggingface_hub import hf_hub_download
from langchain_community.llms import LlamaCpp
from logging import Logger

def HUGGINGFACE_MODEL_CACHE_PATH():
    return os.path.join(
        get_data_dir(),
        'models',
        'huggingface'
    )

# @TODO For nice typing, LLM should be base class, with this in LlamaLLM
class LLM:
    def __init__(self, log: Logger, config: dict) -> None:
        self.config = config
        self.log = log

    def get(self) -> LlamaCpp:
        self.model_filepath = hf_hub_download(
            repo_id=self.config['repo'],
            filename=self.config['filename'],
            cache_dir=HUGGINGFACE_MODEL_CACHE_PATH()
        )
        match self.config['type']:
            case 'llama':
                return self.getLlama()
            case _:
                return None

    def getLlama(self) -> LlamaCpp:
        return LlamaCpp(
            model_path=self.model_filepath,
            max_tokens=self.config['max_response_tokens'],
            n_batch=self.config['n_batch'],
            n_ctx=self.config['n_ctx'],
            n_gpu_layers=self.config['n_gpu_layers'],
            repeat_penalty=self.config['repeat_penalty'],
            temperature=self.config['temperature'],
            top_k=self.config['top_k'],
            top_p=self.config['top_p'],
            verbose=self.config['verbose']
        )
