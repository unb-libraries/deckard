import gc
import psutil
import torch
from secrets import token_hex

def clear_gpu_memory():
    torch.cuda.empty_cache()
    gc.collect()

def gen_uuid():
    return token_hex(32)

def report_memory_use(log):
    process = psutil.Process()
    memory_use = process.memory_info().rss / 1024 / 1024
    log.info(f"Memory use: {memory_use} MB")
