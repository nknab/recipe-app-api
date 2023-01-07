"""
Sample test
"""

from django.test import SimpleTestCase

from app import calc

class CalcTest(SimpleTestCase):

    def test_add_numbers(self):
        res = calc.add(10, 8)

        self.assertEqual(18, res)

    def test_subtract_numbers(self):
        res = calc.subtract(10, 8)

        self.assertEqual(2, res)