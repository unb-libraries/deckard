"""Provides utility functions."""
import gc
from io import TextIOWrapper
from logging import Logger
from secrets import token_hex

import psutil
import pandas as pd
import torch
from bs4 import BeautifulSoup

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

def replace_html_tables_with_csv(text: str) -> str:
    """Replaces HTML table elements with CSV representations.

    Args:
        text (str): The text to process.

    Returns:
        str: The processed text.
    """
    soup = BeautifulSoup(text, 'html.parser')
    for table in soup.find_all('table'):
        list_header = []
        data = []
        caption = ''
        caption = table.find('caption')
        if caption:
            caption = caption.get_text().strip()
        rows = table.find_all('tr')
        first_row = True
        for row in rows:
            if first_row:
                first_row = False
                for item in row:
                    try:
                        list_header.append(item.get_text().strip())
                    except Exception:
                        continue
            else:
                row_data = []
                for data_element in row:
                    try:
                        row_data.append(data_element.get_text().strip())
                    except Exception:
                        continue
                data.append(row_data)
        frame = pd.DataFrame(data = data, columns = list_header)
        table.name = "pre"
        table.string = caption + "\n" + frame.to_csv()
    return str(soup)
