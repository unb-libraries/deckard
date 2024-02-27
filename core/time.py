import datetime

def cur_timestamp():
    return datetime.datetime.now().timestamp()

def time_since(start_time):
    return cur_timestamp() - start_time
