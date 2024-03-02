"""Provides time-related utility functions."""
import datetime

def cur_timestamp() -> float:
    """Returns the current timestamp.

    Returns:
        float: The current timestamp.
    """
    return datetime.datetime.now().timestamp()

def time_since(since_time: float) -> float:
    """Returns the time since the given timestamp.

    Args:
        since_time (float): The timestamp to compare against.

    Returns:
        float: The time since the given timestamp.
    """
    return cur_timestamp() - since_time
