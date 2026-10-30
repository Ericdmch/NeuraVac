"""Roomba 600 cleaning motor command encoding and input validation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.cleaning import cleaning_command


class CleaningTests(unittest.TestCase):
    def test_individual_and_combined_motors(self):
        self.assertEqual(cleaning_command(False, False, False), [138, 0])
        self.assertEqual(cleaning_command(True, False, False), [138, 2])
        self.assertEqual(cleaning_command(False, True, False), [138, 1])
        self.assertEqual(cleaning_command(False, False, True), [138, 4])
        self.assertEqual(cleaning_command(True, True, True), [138, 7])

    def test_rejects_non_boolean_values(self):
        with self.assertRaises(ValueError):
            cleaning_command('true', False, False)
