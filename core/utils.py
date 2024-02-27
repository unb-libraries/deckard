import psutil

def report_memory_use(log):
    process = psutil.Process()
    memory_use = process.memory_info().rss / 1024 / 1024
    log.info(f"Memory use: {memory_use} MB")
