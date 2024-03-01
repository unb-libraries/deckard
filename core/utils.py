import gc
from logging import Logger
import psutil
import torch
from secrets import token_hex

def clear_gpu_memory() -> None:
    torch.cuda.empty_cache()
    gc.collect()

def gen_uuid() -> str:
    return token_hex(32)

def report_memory_use(log: Logger) -> None:
    process = psutil.Process()
    memory_use = process.memory_info().rss / 1024 / 1024
    log.info(f"Memory use: {memory_use} MB")
