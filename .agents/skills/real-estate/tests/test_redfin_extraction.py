"""Regression test for Redfin financial-field extraction.

Feeds a synthetic reactServerState.InitialContext (mirroring Redfin's real
dataCache shapes) through the production parse_property() and asserts that
HOA, property tax (amount + rate), insurance, and schools all come out.

Run: uv run python tests/test_redfin_extraction.py
(no network — this is a pure-parse test against fixtures)
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import redfin_parse as P  # noqa: E402


def _entry(payload):
    """Wrap a payload the way Redfin's dataCache stores it: XSSI-guarded JSON."""
    return {"res": {"text": "{}&&" + json.dumps({"payload": payload})}}


def _fixture_ctx():
    return {
        "ReactServerAgent.cache": {"dataCache": {
            "/stingray/api/home/details/initialInfo?propertyId=1&listingId=2":
                _entry({"propertyId": 1, "listingId": 2}),
            "/stingray/api/home/details/aboveTheFold?propertyId=1&listingId=2":
                _entry({"addressSectionInfo": {
                    "streetAddress": {"assembledAddress": "123 Test St"},
                    "city": "Austin", "state": "TX", "zip": "78704",
                    "priceInfo": {"amount": 700000},
                    "beds": 4, "baths": 3,
                    "sqFt": {"value": 2200}, "yearBuilt": 2019,
                    "hoaDues": 145,
                }}),
            "/stingray/api/v1/home/details/belowTheFold?propertyId=1":
                _entry({"publicRecordsInfo": {"taxInfo": {
                    "taxesDue": 9100, "rollYear": 2025,
                    "taxableLandValue": 200000,
                    "taxableImprovementValue": 480000,
                }}}),
            "/stingray/do/api/costOfHomeOwnershipDetails?propertyId=1":
                _entry({
                    "propertyTax": {"amount": 760},     # monthly
                    "homeInsurance": {"amount": 88},    # monthly
                    "hoa": {"amount": 145},
                }),
            "/stingray/api/v1/home/details/belowTheFold/schoolsAndDistrictsInfo?propertyId=1":
                _entry({"servingThisHomeSchools": [
                    {"name": "Test Elementary", "level": "Elementary", "rating": 8, "distance": 0.3, "grades": "K-5"},
                    {"name": "Test Middle", "level": "Middle", "rating": 6, "distance": 1.1, "grades": "6-8"},
                    {"name": "Test High", "level": "High", "rating": 7, "distance": 0.9, "grades": "9-12"},
                ]}),
        }}
    }


def test_redfin_financial_extraction():
    out = P.parse_property(_fixture_ctx())
    assert out["monthly_hoa_fee"] == 145.0, out.get("monthly_hoa_fee")
    assert out["hoa_per_month"] == 145.0, out.get("hoa_per_month")
    assert out["annual_property_tax"] == 9100.0, out.get("annual_property_tax")
    # rate is surfaced as a PERCENT (9100 / 700000 * 100 = 1.3) to match Zillow
    assert out["property_tax_rate"] == 1.3, out.get("property_tax_rate")
    assert out["annual_homeowners_insurance"] == 1056.0, out.get("annual_homeowners_insurance")  # 88 * 12
    schools = out.get("schools") or []
    assert len(schools) == 3, len(schools)
    assert schools[0]["name"] == "Test Elementary"
    assert schools[0]["rating"] == 8
    assert len(out.get("tax_history") or []) == 1


def test_hoa_falls_back_to_cost_of_ownership():
    """If addressSectionInfo lacks HOA, cost-of-ownership.hoa.amount wins."""
    ctx = _fixture_ctx()
    # Strip the address-section HOA so the only source is cost-of-ownership.
    cache = ctx["ReactServerAgent.cache"]["dataCache"]
    atf_key = next(k for k in cache if "aboveTheFold" in k)
    atf = json.loads(cache[atf_key]["res"]["text"][4:])
    atf["payload"]["addressSectionInfo"].pop("hoaDues", None)
    cache[atf_key]["res"]["text"] = "{}&&" + json.dumps(atf)
    out = P.parse_property(ctx)
    assert out["monthly_hoa_fee"] == 145.0, out.get("monthly_hoa_fee")


def test_tax_rate_from_direct_field():
    """When cost-of-ownership exposes a tax rate directly, use it (normalized)."""
    ctx = _fixture_ctx()
    cache = ctx["ReactServerAgent.cache"]["dataCache"]
    coo_key = next(k for k in cache if "costOfHomeOwnership" in k)
    coo = json.loads(cache[coo_key]["res"]["text"][4:])
    coo["payload"]["propertyTaxRate"] = 2.05  # percent form
    cache[coo_key]["res"]["text"] = "{}&&" + json.dumps(coo)
    out = P.parse_property(ctx)
    assert out["property_tax_rate"] == 2.05, out.get("property_tax_rate")


if __name__ == "__main__":
    test_redfin_financial_extraction()
    test_hoa_falls_back_to_cost_of_ownership()
    test_tax_rate_from_direct_field()
    print("all Redfin extraction tests passed")
