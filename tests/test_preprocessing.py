import unittest
import os
import sys

# Ensure workspace root is in sys.path for both IDE and CLI execution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.preprocessing.card_mapper import CardMapper
from scripts.preprocessing.device_mapper import DeviceMapper

class TestCardMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapper = CardMapper()
        cls.mapper.fit(
            closed_cases_path="d:/HHGOA-Fraud-Agent/closed_cases_history.csv",
            case_pack_path="d:/HHGOA-Fraud-Agent/case_pack.csv",
            transactions_path="d:/HHGOA-Fraud-Agent/transactions.csv"
        )

    def test_benchmark_resolutions(self):
        # Test specific known benchmark cases
        # HHG-001: C12382-K1
        card1 = self.mapper.get_card_id("C12382", "21139", "242.0", "150.0", "visa", "166.0", "debit")
        self.assertEqual(card1, "C12382-K1")

        # HHG-003: C08623-K2
        card3 = self.mapper.get_card_id("C08623", "19739", "470.0", "150.0", "mastercard", "137.0", "credit")
        self.assertEqual(card3, "C08623-K2")

        # HHG-014: C13487-K1
        card14 = self.mapper.get_card_id("C13487", "13250", "445.0", "150.0", "mastercard", "224.0", "debit")
        self.assertEqual(card14, "C13487-K1")

    def test_reproducibility(self):
        # Querying the same signature multiple times must return the same result
        res1 = self.mapper.get_card_id("C04570", "20749", "111.0", "150.0", "mastercard", "224.0", "credit")
        res2 = self.mapper.get_card_id("C04570", "20749", "111.0", "150.0", "mastercard", "224.0", "credit")
        self.assertEqual(res1, res2)

class TestDeviceMapping(unittest.TestCase):
    def test_normalization_and_hash(self):
        c1, id1, attrs1 = DeviceMapper.create_device_profile("  Windows  ", "Windows 10", "chrome 63.0", "1920x1080", "desktop")
        c2, id2, attrs2 = DeviceMapper.create_device_profile("Windows", " Windows 10 ", "chrome 63.0", "1920x1080", "Desktop")
        self.assertEqual(c1, c2)
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("DEV_"))

    def test_missing_values(self):
        c, dev_id, attrs = DeviceMapper.create_device_profile("", "", "", "", "mobile")
        self.assertEqual(c, "Unknown (mobile)")
        self.assertTrue(dev_id.startswith("DEV_"))

    def test_partial_missing(self):
        c, dev_id, attrs = DeviceMapper.create_device_profile("SM-G935F Build/NRD90M", "", "chrome 59.0", "")
        self.assertEqual(c, "SM-G935F Build/NRD90M | Unknown | chrome 59.0 | Unknown")

if __name__ == '__main__':
    unittest.main()
