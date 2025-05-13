"""Provides time-related utility functions."""
import datetime
from typing import List, Dict

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

class TimingManager:
    def __init__(self):
        """
        Initializes the TimingManager with dictionaries to store timings and start times.
        """
        self.timings: Dict[str, float] = {}
        self.start_times: Dict[str, float] = {}
        self.current_timing_id = None
        self.compound_counters: Dict[str, int] = {}

    def __enter__(self):
        if self.current_timing_id:
            self.start_timing([self.current_timing_id])
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.current_timing_id:
            self.finalize_timing([self.current_timing_id])

    def init_timing(self, timing_ids: List[str]):
        """
        Initializes timing entries for the given list of IDs to zero.

        Args:
            timing_ids (list): A list of timing IDs to initialize.
        """
        self.timings.update({timing_id: 0 for timing_id in timing_ids})

    def start_timing(self, timing_ids):
        """
        Records the start times for the given list of timing IDs. If a timing ID was not initialized, it initializes it to zero.

        Args:
            timing_ids (list): A list of timing IDs to start.
        """
        for timing_id in timing_ids:
            if timing_id not in self.timings:
                self.init_timing([timing_id])
            self.start_times[timing_id] = cur_timestamp()

    def finalize_timing(self, timing_ids):
        """
        Finalizes the timings for the given list of IDs based on the elapsed time since their start times.

        Args:
            timing_ids (list): A list of timing IDs to finalize.

        Raises:
            ValueError: If the start time for any given ID is not recorded.
        """
        for timing_id in timing_ids:
            if timing_id not in self.start_times:
                raise ValueError(f"Start time for timing ID '{timing_id}' not recorded.")
            elapsed_time = time_since(self.start_times[timing_id])
            self.timings[timing_id] += elapsed_time
            del self.start_times[timing_id]

    def get_timings(self):
        """
        Returns all stored timings as a dictionary.

        Returns:
            dict: A dictionary of all timing entries.
        """
        return self.timings

    def time_block(self, timing_id: str):
        """
        Sets the current timing ID for use with a context manager.

        Args:
            timing_id (str): The timing ID to track.
        """
        self.current_timing_id = timing_id
        return self

    def reset_timing(self, timing_ids: List[str] = None, keep_ids: List[str] = None):
        """
        Resets the specified timing IDs, all timings if no IDs are provided,
        or all except those in keep_ids.

        Args:
            timing_ids (list): A list of timing IDs to reset. Resets all if None.
            keep_ids (list): A list of timing IDs to keep (do not reset).
        """
        if keep_ids is not None:
            to_remove = [tid for tid in self.timings if tid not in keep_ids]
            for timing_id in to_remove:
                self.timings.pop(timing_id, None)
                self.start_times.pop(timing_id, None)
                self.compound_counters.pop(timing_id, None)
        elif timing_ids is None:
            self.timings.clear()
            self.start_times.clear()
            self.compound_counters.clear()
        else:
            for timing_id in timing_ids:
                self.timings.pop(timing_id, None)
                self.start_times.pop(timing_id, None)
                self.compound_counters.pop(timing_id, None)

    def compound_time_block(self, base_id: str):
        """
        Context manager for timing compound items under a base ID.

        Args:
            base_id (str): The base ID for the compound timing.

        Returns:
            CompoundTimingContext: A context manager for compound timing.
        """
        return CompoundTimingContext(self, base_id)

    def increment_compound_timing(self, base_id: str) -> str:
        """
        Increments the compound timing ID for the given base ID.

        Args:
            base_id (str): The base ID for the compound timing.

        Returns:
            str: The new compound timing ID.
        """
        if base_id not in self.compound_counters:
            self.compound_counters[base_id] = 0
        self.compound_counters[base_id] += 1
        return f"{base_id}-{self.compound_counters[base_id]}"

    def finalize_compound_timing(self, base_id: str):
        """
        Sums up all compound timings under the base ID into a total.

        Args:
            base_id (str): The base ID for the compound timing.
        """
        total_time = sum(
            time for timing_id, time in self.timings.items()
            if timing_id.startswith(f"{base_id}-")
        )
        self.timings[base_id] = total_time


class CompoundTimingContext:
    def __init__(self, manager: TimingManager, base_id: str):
        self.manager = manager
        self.base_id = base_id
        self.current_compound_id = None

    def __enter__(self):
        self.current_compound_id = self.manager.increment_compound_timing(self.base_id)
        self.manager.start_timing([self.current_compound_id])
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.manager.finalize_timing([self.current_compound_id])
        self.manager.finalize_compound_timing(self.base_id)
