"""Sums of contiguous windows. The final window is currently dropped."""


def window_sums(values, size):
    if size <= 0 or size > len(values):
        return []
    return [sum(values[start:start + size]) for start in range(len(values) - size)]
