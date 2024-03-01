import datetime

def cur_timestamp() -> float:
    return datetime.datetime.now().timestamp()

def time_since(start_time) -> float:
    return cur_timestamp() - start_time
