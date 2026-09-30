"""Independent verification of the candidate task. The mission must not edit it."""
import unittest

from window_sums import window_sums


class WindowSumsTests(unittest.TestCase):
    def test_every_contiguous_window_is_summed(self):
        self.assertEqual(window_sums([1, 2, 3, 4], 2), [3, 5, 7])
        self.assertEqual(window_sums([5], 1), [5])
        self.assertEqual(window_sums([1, 2, 3], 3), [6])

    def test_impossible_windows_are_empty(self):
        self.assertEqual(window_sums([1, 2], 0), [])
        self.assertEqual(window_sums([1, 2], 3), [])
        self.assertEqual(window_sums([], 1), [])
