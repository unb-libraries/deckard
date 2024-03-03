"""Provides utility functions."""
import gc
from io import TextIOWrapper
from logging import Logger
from secrets import token_hex

import psutil
import torch

def clear_gpu_memory() -> None:
    """Clears the memory of the GPU."""
    torch.cuda.empty_cache()
    gc.collect()

def gen_uuid() -> str:
    """Generates a UUID.

    Returns:
        str: The generated UUID.
    """
    return token_hex(32)

def short_uuid(uuid) -> str:
    """Shortens a UUID.

    Args:
        uuid (str): The UUID to shorten.

    Returns:
        str: The shortened UUID.
    """
    return uuid[:8]

def report_memory_use(log: Logger) -> None:
    """Reports the memory use.

    Args:
        log (Logger): The logger to use for reporting.
    """
    process = psutil.Process()
    memory_use = process.memory_info().rss / 1024 / 1024
    log.info("Memory use: %s MB", memory_use)

def open_file_read(file_path: str) -> TextIOWrapper:
    """Opens a file for reading.

    Args:
        file_path (str): The path to the file.

    Returns:
        TextIOWrapper: The file object.
    """
    return open(file_path, 'r', encoding="utf-8")

def open_file_write(file_path: str) -> TextIOWrapper:
    """Opens a file for writing.

    Args:
        file_path (str): The path to the file.

    Returns:
        TextIOWrapper: The file object.
    """
    return open(file_path, 'w', encoding="utf-8")
