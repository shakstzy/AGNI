"""Pure-parse Redfin extractors. NO HTTP, NO subprocess, NO env reads.

Every function in this module takes already-fetched data (HTML string,
parsed InitialContext dict, or a cache entry dict) and returns plain
Python data. This is what tests should target. The fetch logic in
redfin.py composes these with HTTP.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlparse

XSSI_PREFIX = "{}&&"
BASE = "https://www.redfin.com"


def _payload(entry: dict | None):
    if not entry:
        return None
    return entry.get("payload")


def _payload_dict(entry: dict | None) -> dict:
    p = _payload(entry)
    return p if isinstance(p, dict) else {}


def _payload_list(entry: dict | None) -> list:
    p = _payload(entry)
    return p if isinstance(p, list) else []


INITIAL_CTX_RE = re.compile(
    r"reactServerState\.InitialContext\s*=\s*(\{.*?\});", re.DOTALL
)
CITY_URL_RE = re.compile(r"/city/(\d+)/([A-Z]{2})/([^/]+)")
ZIP_URL_RE = re.compile(r"/zipcode/(\d+)")
NEIGHBORHOOD_URL_RE = re.compile(r"/neighborhood/(\d+)/")
PROPERTY_URL_RE = re.compile(r"/[A-Z]{2}/[^/]+/[^/]+/home/(\d+)")

GIS_REGION_TYPE = {"city": 6, "zip": 2, "neighborhood": 1, "county": 5, "state": 4}

_PROPERTY_TYPE_BY_CODE = {
    1: "single-family", 2: "condo", 3: "townhouse",
    4: "multi-family", 5: "land", 6: "other",
    7: "mobile", 8: "co-op",
}


def initial_context(html: str) -> dict:
    m = INITIAL_CTX_RE.search(html)
    if not m:
        raise RuntimeError("redfin: reactServerState.InitialContext not in HTML; layout changed?")
    return json.loads(m.group(1))


def cache_entry(ctx: dict, path_prefix: str) -> dict | None:
    cache = (ctx.get("ReactServerAgent.cache") or {}).get("dataCache") or {}
    for key, entry in cache.items():
        if not key.startswith(path_prefix):
            continue
        text = ((entry.get("res") or {}).get("text")) or ""
        if text.startswith(XSSI_PREFIX):
            text = text[len(XSSI_PREFIX):]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue
    return None


def cache_keys(ctx: dict) -> list[str]:
    cache = (ctx.get("ReactServerAgent.cache") or {}).get("dataCache") or {}
    return sorted(cache.keys())


def parse_region_from_url(url_or_path: str) -> dict:
    path = urlparse(url_or_path).path or url_or_path
    if m := CITY_URL_RE.search(path):
        return {"region_id": int(m.group(1)),
                "region_type": GIS_REGION_TYPE["city"],
                "kind": "city", "state": m.group(2), "name": m.group(3),
                "url": BASE + f"/city/{m.group(1)}/{m.group(2)}/{m.group(3)}"}
    if m := ZIP_URL_RE.search(path):
        return {"region_id": int(m.group(1)),
                "region_type": GIS_REGION_TYPE["zip"],
                "kind": "zip", "url": BASE + f"/zipcode/{m.group(1)}"}
    if m := NEIGHBORHOOD_URL_RE.search(path):
        return {"region_id": int(m.group(1)),
                "region_type": GIS_REGION_TYPE["neighborhood"],
                "kind": "neighborhood", "url": BASE + path}
    raise RuntimeError(f"redfin: URL {url_or_path!r} doesn't match a known region pattern")


def summarize_home(h: dict) -> dict:
    addr = h.get("streetLine") or {}
    price = h.get("price") or {}
    hoa = h.get("hoa") or {}
    code = h.get("propertyType")
    lat_long = h.get("latLong") or {}
    lat = lat_long.get("latitude") if isinstance(lat_long, dict) else None
    lng = lat_long.get("longitude") if isinstance(lat_long, dict) else None
    if lat is None and isinstance(lat_long, dict):
        v = lat_long.get("value") or {}
        lat, lng = v.get("latitude"), v.get("longitude")
    photos = h.get("photos") or {}
    photo_urls: list[str] = []
    if isinstance(photos, dict):
        for item in (photos.get("items") or []):
            for u in (item.get("photoUrls") or {}).values():
                if isinstance(u, str) and u.startswith("http"):
                    photo_urls.append(u)
                    break
    return {
        "mls_id": h.get("mlsId"),
        "property_id": h.get("propertyId"),
        "listing_id": h.get("listingId"),
        "address": addr.get("value") if isinstance(addr, dict) else h.get("streetLine"),
        "city": h.get("city"),
        "state": (h.get("state") or {}).get("value") if isinstance(h.get("state"), dict) else h.get("state"),
        "zip": h.get("zip"),
        "price": price.get("value") if isinstance(price, dict) else price,
        "price_per_sqft": (h.get("pricePerSqFt") or {}).get("value") if isinstance(h.get("pricePerSqFt"), dict) else h.get("pricePerSqFt"),
        "beds": h.get("beds"),
        "baths": h.get("baths"),
        "sqft": (h.get("sqFt") or {}).get("value") if isinstance(h.get("sqFt"), dict) else h.get("sqFt"),
        "lot_size": (h.get("lotSize") or {}).get("value") if isinstance(h.get("lotSize"), dict) else h.get("lotSize"),
        "year_built": (h.get("yearBuilt") or {}).get("value") if isinstance(h.get("yearBuilt"), dict) else h.get("yearBuilt"),
        "hoa_per_month": hoa.get("value") if isinstance(hoa, dict) else hoa,
        "url": f"{BASE}{h.get('url')}" if h.get("url") and not h.get("url", "").startswith("http") else h.get("url"),
        "status": h.get("mlsStatus"),
        "listing_type": h.get("listingType"),
        "property_type": _PROPERTY_TYPE_BY_CODE.get(code) if isinstance(code, int) else None,
        "days_on_market": (h.get("timeOnRedfin") or {}).get("days") if isinstance(h.get("timeOnRedfin"), dict) else None,
        "lat": lat,
        "lng": lng,
        "photo_url": photo_urls[0] if photo_urls else None,
        "photo_count": len(photo_urls) or None,
    }


def parse_search_homes(ctx: dict) -> list[dict]:
    gis_resp = cache_entry(ctx, "/stingray/api/gis?")
    if not gis_resp:
        return []
    homes = ((gis_resp.get("payload") or {}).get("homes")) or []
    return [summarize_home(h) for h in homes]


def parse_csv(text: str) -> list[dict]:
    import csv
    import io
    reader = csv.DictReader(io.StringIO(text))
    out = []
    for row in reader:
        if not (row.get("ADDRESS") or "").strip():
            continue
        out.append({
            "address": row.get("ADDRESS"),
            "city": row.get("CITY"),
            "state": row.get("STATE OR PROVINCE"),
            "zip": row.get("ZIP OR POSTAL CODE"),
            "price": _to_int(row.get("PRICE")),
            "beds": _to_int(row.get("BEDS")),
            "baths": _to_float(row.get("BATHS")),
            "sqft": _to_int(row.get("SQUARE FEET")),
            "lot_size": _to_int(row.get("LOT SIZE")),
            "year_built": _to_int(row.get("YEAR BUILT")),
            "url": row.get("URL (SEE https://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)") or row.get("URL"),
            "status": row.get("STATUS"),
            "property_type": row.get("PROPERTY TYPE"),
            "days_on_market": _to_int(row.get("DAYS ON MARKET")),
            "hoa_per_month": _to_int(row.get("HOA/MONTH")),
            "price_per_sqft": _to_float(row.get("$/SQUARE FEET")),
            "lat": _to_float(row.get("LATITUDE")),
            "lng": _to_float(row.get("LONGITUDE")),
            "mls_id": (row.get("MLS#") or "").strip() or None,
            "source_mls": (row.get("SOURCE") or "").strip() or None,
        })
    return out


def _to_int(v):
    if v in (None, ""):
        return None
    if isinstance(v, str):
        v = v.replace("$", "").replace(",", "").strip()
        if not v:
            return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _to_float(v):
    if v in (None, ""):
        return None
    if isinstance(v, str):
        v = v.replace("$", "").replace(",", "").strip()
        if not v:
            return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_property(ctx: dict, *, include_raw: bool = False) -> dict:
    initial = cache_entry(ctx, "/stingray/api/home/details/initialInfo") or {}
    above = cache_entry(ctx, "/stingray/api/home/details/aboveTheFold") or {}
    below = (cache_entry(ctx, "/stingray/api/v1/home/details/belowTheFold")
             or cache_entry(ctx, "/stingray/api/home/details/belowTheFold")
             or {})
    avm = cache_entry(ctx, "/stingray/api/home/details/avm") or {}
    avm_hist = cache_entry(ctx, "/stingray/api/home/details/avmHistoricalData") or {}
    rental = cache_entry(ctx, "/stingray/api/home/details/rental-estimate") or {}
    similars = cache_entry(ctx, "/stingray/api/home/details/similars/listings") or {}
    schools_resp = (cache_entry(ctx, "/stingray/api/v1/home/details/belowTheFold/schoolsAndDistrictsInfo")
                    or {})
    risk = cache_entry(ctx, "/stingray/api/v1/home/details/belowTheFold/riskFactorData") or {}
    main_house = cache_entry(ctx, "/stingray/api/home/details/main") or {}
    main_panel = cache_entry(ctx, "/stingray/api/home/details/mainHouseInfoPanelInfo") or {}
    ai_summary = cache_entry(ctx, "/stingray/api/home/details/aiSummary") or {}
    ai_details = cache_entry(ctx, "/stingray/api/v1/home/details/belowTheFold/aiPropertyDetailsInfo") or {}
    commute = cache_entry(ctx, "/stingray/api/home/details/commute/commuteInfo") or {}
    market_insights = cache_entry(ctx, "/stingray/api/home/details/marketInsightsInfo") or {}
    weather = cache_entry(ctx, "/stingray/api/home/details/monthly-weather-averages") or {}
    nearby_oh = cache_entry(ctx, "/stingray/api/home/details/nearbyOpenHouses") or {}
    neighborhood_stats = cache_entry(ctx, "/stingray/api/home/details/neighborhoodStats/statsInfo") or {}
    newest_nearby = cache_entry(ctx, "/stingray/api/home/details/newest-listings-nearby") or {}
    parcel_boundaries = cache_entry(ctx, "/stingray/api/home/details/parcel-boundaries") or {}
    parcel_info = cache_entry(ctx, "/stingray/api/home/details/propertyParcelInfo") or {}
    zoning = cache_entry(ctx, "/stingray/api/home/details/web/parcel-zoning") or {}
    popularity = cache_entry(ctx, "/stingray/api/home/details/popularityInfo") or {}
    price_drop = cache_entry(ctx, "/stingray/api/home/details/priceDropInfo") or {}
    location_score = cache_entry(ctx, "/stingray/api/v1/home/details/location-score") or {}
    sun_exposure = cache_entry(ctx, "/stingray/api/v1/home/details/sun-exposure") or {}
    permits = cache_entry(ctx, "/stingray/api/v2/home/details/permits") or {}
    tour_insights = cache_entry(ctx, "/stingray/api/home/details/tourInsights") or {}
    buying_power = cache_entry(ctx, "/stingray/api/v1/home/details/belowTheFold/buyingPowerInfo") or {}
    home_tags = cache_entry(ctx, "/stingray/api/v1/home/details/belowTheFold/homeHighlightTagsInfo") or {}
    listing_status_banner = cache_entry(ctx, "/stingray/api/home/details/listingStatusBannerInfo/v1") or {}
    activity = cache_entry(ctx, "/stingray/api/home/details/activityData") or {}
    around_home = cache_entry(ctx, "/stingray/api/home/details/aroundThisHomeSectionInfo") or {}
    comp_tags = cache_entry(ctx, "/stingray/api/home/details/compHomeTags/compHomeTagsInfo") or {}
    hot_market = cache_entry(ctx, "/stingray/api/home/details/hotMarketInfo") or {}
    local_insights = cache_entry(ctx, "/stingray/api/home/details/localInsights") or {}
    agents_toured = cache_entry(ctx, "/stingray/api/home/details/tours/agentsWhoToured") or {}
    shared_region = cache_entry(ctx, "/stingray/api/region/shared-region-info") or {}
    page_tags = cache_entry(ctx, "/stingray/api/home/details/v1/pagetagsinfo") or {}
    photo_tags = None
    cache = (ctx.get("ReactServerAgent.cache") or {}).get("dataCache") or {}
    for k in cache:
        if k.startswith("/stingray/api/photoTagsAndCaptions/"):
            photo_tags = cache_entry(ctx, k.split("?")[0])
            break
    primary_region = cache_entry(ctx, "/stingray/api/home/details/primaryRegionInfo") or {}
    # Cost-of-ownership has the monthly tax / insurance / HOA breakouts Redfin
    # shows on the listing page. Cached under the `do/api/...` prefix, not the
    # `api/home/details/...` prefix used by most endpoints.
    cost_own = (cache_entry(ctx, "/stingray/do/api/costOfHomeOwnershipDetails")
                or cache_entry(ctx, "/stingray/api/home/details/costOfHomeOwnership")
                or {})

    p_initial = initial.get("payload") or {}
    p_above = above.get("payload") or {}
    p_below = below.get("payload") or {}
    p_avm = avm.get("payload") or {}
    p_main = main_house.get("payload") or {}
    p_panel = main_panel.get("payload") or {}
    p_panel_main = p_panel.get("mainHouseInfo") or {}
    p_cost_own = cost_own.get("payload") or {}

    asi = p_above.get("addressSectionInfo") or {}
    listing_info = (p_above.get("listingAgents") or {})
    if not listing_info:
        listing_info = p_main.get("mainHouseInfo") or p_panel_main or {}
    history_events = ((p_below.get("propertyHistoryInfo") or {}).get("events")) or []
    public_records = p_below.get("publicRecordsInfo") or {}
    media = (p_above.get("mediaBrowserInfoBySection") or {}).get("photosInfo") or {}
    photo_count = media.get("photoCount") or media.get("totalCount") or None
    photos: list[str] = []
    items = ((media.get("photoBrowser") or {}).get("items") or
             media.get("items") or [])
    for it in items:
        urls = it.get("photoUrls") or {}
        if isinstance(urls, dict):
            for k in ("fullScreen", "fullScreenPhotoUrl", "nonFullScreen", "thumbnail"):
                if isinstance(urls.get(k), str) and urls[k].startswith("http"):
                    photos.append(urls[k])
                    break

    above_la = p_above.get("listingAgents")
    if isinstance(above_la, dict):
        agents = above_la.get("agents") or []
    elif isinstance(above_la, list):
        agents = above_la
    else:
        agents = []
    if not agents:
        panel_la = p_panel_main.get("listingAgents")
        agents = panel_la if isinstance(panel_la, list) else []
    if not agents:
        main_la = (p_main.get("mainHouseInfo") or {}).get("listingAgents")
        agents = main_la if isinstance(main_la, list) else []
    raw_agent = (agents[0] if agents else {}) or {}
    if not isinstance(raw_agent, dict):
        raw_agent = {}
    agent_info = raw_agent.get("agentInfo") if isinstance(raw_agent.get("agentInfo"), dict) else {}
    listing_agent = {
        "name": agent_info.get("agentName") or raw_agent.get("agentName"),
        "license": agent_info.get("licenseNumber") or raw_agent.get("licenseNumber"),
        "email": agent_info.get("emailAddress") or raw_agent.get("emailAddress"),
        "phone": (agent_info.get("redfinPhoneNumber") or agent_info.get("phoneNumber")
                  or raw_agent.get("redfinPhoneNumber") or raw_agent.get("phoneNumber")),
        "brokerage": raw_agent.get("brokerName") or raw_agent.get("brokerage"),
        "is_redfin_agent": agent_info.get("isRedfinAgent") or raw_agent.get("isRedfinAgent"),
    }
    if not any(v for v in listing_agent.values()):
        listing_agent = None

    price_history: list[dict] = []
    tax_history: list[dict] = []
    for ev in history_events:
        eh = {
            "date_epoch_ms": ev.get("eventDate"),
            "event": ev.get("eventDescription"),
            "mls_status": ev.get("mlsDescription"),
            "price": ev.get("price"),
            "source": ev.get("source"),
            "history_event_type": ev.get("historyEventType"),
        }
        if (ev.get("historyEventType") == 9) or (
            isinstance(ev.get("eventDescription"), str)
            and "tax" in ev["eventDescription"].lower()
        ):
            tax_history.append(eh)
        elif ev.get("price") is not None or "list" in (ev.get("eventDescription") or "").lower() \
                or "sold" in (ev.get("eventDescription") or "").lower() \
                or "price" in (ev.get("eventDescription") or "").lower():
            price_history.append(eh)
    if not tax_history and isinstance(public_records.get("taxInfo"), dict):
        ti = public_records["taxInfo"]
        tax_history = [{
            "year": ti.get("rollYear"),
            "taxes_due": ti.get("taxesDue"),
            "taxable_land_value": ti.get("taxableLandValue"),
            "taxable_improvement_value": ti.get("taxableImprovementValue"),
            "source": "redfin_publicRecordsInfo",
        }]

    p_similars = (similars or {}).get("payload") or {}
    nearby_homes_raw = p_similars.get("homes")
    if not isinstance(nearby_homes_raw, list):
        nearby_homes_raw = []
    nearby_homes = []
    for h in nearby_homes_raw[:25]:
        if not isinstance(h, dict):
            continue
        addr = h.get("streetLine") or h.get("addressLine1") or {}
        if isinstance(addr, dict):
            addr = addr.get("value")
        nearby_homes.append({
            "address": addr,
            "city": h.get("city"),
            "state": h.get("state"),
            "zip": h.get("zip"),
            "price": (h.get("price") or {}).get("value") if isinstance(h.get("price"), dict) else h.get("price"),
            "sqft": (h.get("sqFt") or {}).get("value") if isinstance(h.get("sqFt"), dict) else h.get("sqFt"),
            "beds": h.get("beds"),
            "baths": h.get("baths"),
            "url": h.get("url"),
            "mls_status": h.get("mlsStatus"),
        })

    own_oh = ((p_panel.get("openHouseInfo") or {}).get("openHouseList")
              or (p_above.get("openHouseInfo") or {}).get("openHouseList")
              or [])
    nearby_oh_homes = (_payload_dict(nearby_oh).get("homes")) or []
    open_houses = list(own_oh)

    out = {
        "source": "redfin",
        "property_id": p_initial.get("propertyId") or asi.get("propertyId"),
        "listing_id": p_initial.get("listingId") or asi.get("listingId"),
        "status": (asi.get("status") or {}).get("displayValue") if isinstance(asi.get("status"), dict) else asi.get("status"),
        "address": (asi.get("streetAddress") or {}).get("assembledAddress") if isinstance(asi.get("streetAddress"), dict) else asi.get("streetAddress"),
        "city": asi.get("city"),
        "state": asi.get("state"),
        "zip": asi.get("zip"),
        "lat_long": asi.get("latLong"),
        "lat": (asi.get("latLong") or {}).get("latitude") if isinstance(asi.get("latLong"), dict) else None,
        "lng": (asi.get("latLong") or {}).get("longitude") if isinstance(asi.get("latLong"), dict) else None,
        "country": asi.get("countryCode"),
        "price": (asi.get("priceInfo") or {}).get("amount") if isinstance(asi.get("priceInfo"), dict) else asi.get("price"),
        "list_price": asi.get("listingPrice") or (asi.get("priceInfo") or {}).get("amount"),
        "price_per_sqft": asi.get("pricePerSqFt"),
        "beds": asi.get("beds"),
        "baths": asi.get("baths"),
        "full_baths": asi.get("numFullBaths"),
        "half_baths": asi.get("numPartialBaths"),
        "sqft": (asi.get("sqFt") or {}).get("value") if isinstance(asi.get("sqFt"), dict) else asi.get("sqFt"),
        "year_built": asi.get("yearBuilt"),
        "lot_size": asi.get("lotSize"),
        "lot_size_sqft": (asi.get("lotSize") or {}).get("value") if isinstance(asi.get("lotSize"), dict) else asi.get("lotSize"),
        "property_type_code": asi.get("propertyType"),
        "property_type": _PROPERTY_TYPE_BY_CODE.get(asi.get("propertyType")) if isinstance(asi.get("propertyType"), int) else None,
        "list_date": asi.get("listingDate") or asi.get("originalListDate"),
        "sold_date": asi.get("soldDate"),
        "days_on_market": asi.get("daysOnRedfin") or asi.get("dom"),
        "cumulative_days_on_market": asi.get("cumulativeDaysOnRedfin"),
        "redfin_estimate": p_avm.get("predictedValue") or (p_avm.get("predictedPrice") or {}).get("amount"),
        "rent_estimate": (rental.get("payload") or {}).get("predictedValue"),
        "history": history_events,
        "price_history": price_history,
        "tax_history": tax_history,
        "public_records": public_records,
        "tax_info": public_records.get("allTaxInfo") or public_records.get("taxInfo"),
        "apn": public_records.get("apn"),
        "nearby_homes": nearby_homes,
        "schools": (
            _payload_dict(schools_resp).get("servingThisHomeSchools")
            or _payload_dict(schools_resp).get("schoolsToShowOnDP")
            or _payload_dict(schools_resp).get("schools")
            or []
        ),
        "school_districts": _payload_dict(schools_resp).get("districtsServingThisHome") or [],
        "risk_factors": (risk.get("payload") or {}),
        "comps": _summarize_comps(similars),
        "amenities": p_below.get("amenitiesInfo") or {},
        "description": p_above.get("marketingRemarks") or p_main.get("publicRemarks"),
        "listing_agent": listing_agent,
        "mls_source": p_main.get("mlsId") or p_main.get("listingMls"),
        "photos": photos,
        "photo_count": photo_count or len(photos) or None,
        "open_houses": open_houses,
        "nearby_open_houses": nearby_oh_homes,
    }
    ai_summary_payload = _payload(ai_summary)
    if isinstance(ai_summary_payload, dict):
        out["ai_summary"] = ai_summary_payload.get("summary") or ai_summary_payload
    else:
        out["ai_summary"] = ai_summary_payload
    out["ai_property_details"] = _payload_dict(ai_details)
    out["commute"] = _payload_dict(commute)
    out["market_insights"] = _payload_dict(market_insights)
    out["weather"] = _payload_dict(weather)
    out["nearby_open_houses"] = _payload_dict(nearby_oh).get("openHouses") or []
    out["neighborhood_stats"] = _payload_dict(neighborhood_stats)
    out["newest_listings_nearby"] = _payload_dict(newest_nearby).get("homes") or []
    out["parcel_boundaries"] = _payload_dict(parcel_boundaries)
    out["parcel_info"] = _payload_dict(parcel_info)
    out["zoning"] = _payload_dict(zoning)
    out["popularity"] = _payload_dict(popularity)
    out["price_drop"] = _payload_dict(price_drop)
    out["location_score"] = _payload_dict(location_score)
    ls = out["location_score"]
    if isinstance(ls, dict):
        out["walk_score"] = ls.get("walkScore") or (ls.get("walkability") or {}).get("score")
        out["transit_score"] = ls.get("transitScore") or (ls.get("transit") or {}).get("score")
        out["bike_score"] = ls.get("bikeScore") or (ls.get("bike") or {}).get("score")
    out["sun_exposure"] = _payload_dict(sun_exposure)
    out["permits"] = _payload_dict(permits)
    out["tour_insights"] = _payload_dict(tour_insights)
    out["buying_power"] = _payload_dict(buying_power)
    home_tags_payload = _payload(home_tags)
    if isinstance(home_tags_payload, list):
        out["home_highlight_tags"] = home_tags_payload
    elif isinstance(home_tags_payload, dict):
        out["home_highlight_tags"] = home_tags_payload.get("homeHighlightTags") or []
    else:
        out["home_highlight_tags"] = []
    out["listing_status_banner"] = _payload_dict(listing_status_banner)
    out["avm_historical"] = _payload_dict(avm_hist)
    out["main_house_panel"] = _payload_dict(main_panel)
    activity_payload = _payload_dict(activity)
    out["total_views"] = activity_payload.get("totalViews")
    out["favorite_count"] = activity_payload.get("favoriteCount")
    out["activity_listing_date"] = activity_payload.get("listingDate")
    around = _payload_dict(around_home)
    walk_data = around.get("walkScoreData") or {}
    if isinstance(walk_data, dict):
        out["walk_score"] = out.get("walk_score") or walk_data.get("walkScore")
        out["transit_score"] = out.get("transit_score") or walk_data.get("transitScore")
        out["bike_score"] = out.get("bike_score") or walk_data.get("bikeScore")
    out["points_of_interest"] = around.get("pointOfInterestList") or []
    out["transit_data"] = around.get("transitData")
    out["region_name"] = around.get("regionName")
    out["comp_home_tags"] = _payload_dict(comp_tags)
    out["hot_market"] = _payload_dict(hot_market)
    out["local_insights"] = _payload_dict(local_insights)
    out["agents_who_toured"] = _payload_dict(agents_toured)
    sr = _payload_dict(shared_region)
    out["region_trends"] = sr.get("trendsData")
    out["region_compete_score"] = sr.get("competeScoreResponse")
    out["region_offer_insights"] = sr.get("offerInsightsInfo")
    out["region_aggregate_trends"] = sr.get("aggregateTrendsData")
    out["region_breadcrumbs"] = sr.get("regionBreadcrumbs") or []
    out["primary_region"] = _payload_dict(primary_region)
    pt = _payload_dict(page_tags)
    out["seo_meta_tags"] = pt.get("metaTags") or []
    out["page_title"] = pt.get("pageTitle")
    if photo_tags:
        ptp = _payload_dict(photo_tags)
        out["photo_tags_by_id"] = ptp.get("tagsByPhotoId") or {}
        out["photo_filter_tags"] = ptp.get("includedFilterTags") or []

    # --- Cost-of-ownership and HOA: flat fields matching Zillow's naming so
    #     the aggregate view can compare/average across sources.
    out["cost_of_home_ownership"] = p_cost_own

    # Monthly HOA. Redfin scatters this across several payloads; check in
    # priority order: above-the-fold address section, main-house-info panel,
    # cost-of-ownership breakout.
    hoa_monthly = _extract_dollar_amount(
        asi.get("hoaDues"),
        asi.get("hoaFee"),
        asi.get("monthlyHoaDues"),
        p_panel_main.get("hoaDues"),
        p_panel_main.get("monthlyHoaDues"),
        p_cost_own.get("hoaDues"),
        (p_cost_own.get("hoa") or {}).get("amount") if isinstance(p_cost_own.get("hoa"), dict) else None,
    )
    if hoa_monthly is not None:
        out["monthly_hoa_fee"] = hoa_monthly
        out["hoa_per_month"] = hoa_monthly  # alias for cross-source aggregation

    # Annual property tax (dollar amount). Cost-of-ownership reports it
    # monthly; publicRecordsInfo.taxInfo reports it annually as `taxesDue`.
    monthly_tax = _extract_dollar_amount(
        (p_cost_own.get("propertyTax") or {}).get("amount") if isinstance(p_cost_own.get("propertyTax"), dict) else None,
        p_cost_own.get("propertyTaxMonthly"),
    )
    annual_tax = _extract_dollar_amount(
        p_cost_own.get("annualPropertyTax"),
        (public_records.get("taxInfo") or {}).get("taxesDue") if isinstance(public_records.get("taxInfo"), dict) else None,
    )
    if annual_tax is None and monthly_tax is not None:
        annual_tax = monthly_tax * 12.0
    if annual_tax is not None:
        out["annual_property_tax"] = round(annual_tax, 2)

    # Property tax RATE. Surface as a PERCENT number (e.g. 2.10 means
    # 2.10%) to match Zillow's `property_tax_rate` convention. Cashflow
    # normalizes percent->fraction downstream regardless of which source
    # reported it.
    tax_rate_fraction = None
    rate_direct = _extract_dollar_amount(
        p_cost_own.get("propertyTaxRate"),
        p_cost_own.get("propertyTaxPercent"),
    )
    if rate_direct is not None:
        tax_rate_fraction = rate_direct / 100.0 if rate_direct > 1 else rate_direct
    elif annual_tax is not None and out.get("price"):
        try:
            price_num = float(out["price"])
            if price_num > 0:
                tax_rate_fraction = annual_tax / price_num
        except (TypeError, ValueError):
            pass
    if tax_rate_fraction is not None:
        out["property_tax_rate"] = round(tax_rate_fraction * 100, 4)

    # Annual homeowners insurance estimate from cost-of-ownership.
    monthly_ins = _extract_dollar_amount(
        (p_cost_own.get("homeInsurance") or {}).get("amount") if isinstance(p_cost_own.get("homeInsurance"), dict) else None,
        (p_cost_own.get("homeownersInsurance") or {}).get("amount") if isinstance(p_cost_own.get("homeownersInsurance"), dict) else None,
        p_cost_own.get("homeInsuranceMonthly"),
    )
    annual_ins = _extract_dollar_amount(
        p_cost_own.get("annualHomeInsurance"),
        p_cost_own.get("annualHomeownersInsurance"),
    )
    if annual_ins is None and monthly_ins is not None:
        annual_ins = monthly_ins * 12.0
    if annual_ins is not None:
        out["annual_homeowners_insurance"] = round(annual_ins, 2)

    if include_raw:
        out["raw"] = {
            "initial": p_initial, "above": p_above, "below": p_below,
            "avm": p_avm, "similars": similars, "main": p_main,
            "cost_of_home_ownership": p_cost_own,
        }
    return out


def _extract_dollar_amount(*candidates) -> float | None:
    """Pick the first non-null numeric value from a list of candidates.

    Each candidate can be a number, a string (with $/,/whitespace), or a
    dict like {"amount": 350, "currency": "USD"} / {"value": 350} which
    Redfin sometimes wraps money values in. Returns float or None.
    """
    for c in candidates:
        if c is None:
            continue
        if isinstance(c, (int, float)):
            return float(c)
        if isinstance(c, str):
            s = c.replace("$", "").replace(",", "").strip()
            if not s:
                continue
            try:
                return float(s)
            except ValueError:
                continue
        if isinstance(c, dict):
            for k in ("amount", "value", "monthly", "annual"):
                v = c.get(k)
                if v is not None:
                    return _extract_dollar_amount(v)
    return None


def _summarize_comps(similars: dict) -> list[dict]:
    homes = ((similars.get("payload") or {}).get("homes")) or []
    return [summarize_home(h) for h in homes][:20]
