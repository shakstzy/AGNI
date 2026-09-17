"""Unit tests for Apify CLI and People Search Adapter."""

import unittest
from pathlib import Path
import sys

# Add parent directory to path
SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from adapters.people_search import clean_phone, extract_e164, normalize_item


class TestPeopleSearchAdapter(unittest.TestCase):
    def test_clean_phone(self):
        self.assertEqual(clean_phone("(516) 781-7770"), "5167817770")
        self.assertEqual(clean_phone("+1-516-781-7770"), "5167817770")
        self.assertEqual(clean_phone("15167817770"), "5167817770")
        self.assertEqual(clean_phone("5167817770"), "5167817770")

    def test_extract_e164(self):
        text = "(516) 781-7770 - Landline Possible Primary Phone"
        extracted = extract_e164(text)
        self.assertEqual(extracted, ["(516) 781-7770"])

    def test_normalize_item_tps(self):
        raw_tps = {
            "fullName": "Cyrinus Kent",
            "age": 68,
            "currentAddress": "Wantagh, NY 11793",
            "pastAddresses": ["Brentwood, NY 11717"],
            "phones": ["(516) 781-7770 - Landline"],
            "emails": ["cyrinus@example.com"],
            "relatives": ["Heidi Kent Age 62"],
            "associates": ["Bruce Popko Age 69"],
            "profileUrl": "https://www.truepeoplesearch.com/find/person/px46004rn2640u8r6rr4",
            "source": "truepeoplesearch",
        }
        res = normalize_item(raw_tps)
        self.assertEqual(res["full_name"], "Cyrinus Kent")
        self.assertEqual(res["age"], 68)
        self.assertEqual(res["current_address"], "Wantagh, NY 11793")
        self.assertEqual(res["phones"], ["(516) 781-7770 - Landline"])
        self.assertEqual(res["emails"], ["cyrinus@example.com"])
        self.assertEqual(res["source"], "truepeoplesearch")


if __name__ == "__main__":
    unittest.main()
