"""
Timeshare Rental Deal Scanner
Parses timeshare rental listings from TUG2 (Timeshare Users Group), calculates 
deal scores by comparing listing prices to retail resort valuations, and generates 
a structured data feed for the web dashboard.
"""

import os
import sys
import json
import time
import re
import socket
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Attempt to import BeautifulSoup, fallback if not present
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# Set global timeout
socket.setdefaulttimeout(30)

# Target Directory for web data
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
DEALS_JSON_PATH = os.path.join(WEB_DIR, "deals.json")

# Ensure docs directory exists
os.makedirs(WEB_DIR, exist_ok=True)

# ── Retail Resort Benchmarks & TUG ResortIds ────────────────────────────────
# Retail cost averages per night for popular timeshare properties.
# tug_resort_id: numeric ID used in TUG Marketplace GET search URLs.
#   URL format: https://tug2.com/timesharemarketplace/search?ResortId=NNNN&ForRent=True
RESORT_RETAIL_BENCHMARKS = {
    "Marriott's Maui Ocean Club": {"retail_per_night": 750, "brand": "Marriott", "location": "Maui, Hawaii", "tug_resort_id": 13881},
    "Westin Kaanapali Ocean Resort Villas": {"retail_per_night": 850, "brand": "Westin", "location": "Maui, Hawaii", "tug_resort_id": 13901},
    "Disney's Aulani Resort & Spa": {"retail_per_night": 900, "brand": "Disney Vacation Club", "location": "Oahu, Hawaii", "tug_resort_id": 15365},
    "Marriott's Ko Olina Beach Club": {"retail_per_night": 650, "brand": "Marriott", "location": "Oahu, Hawaii", "tug_resort_id": 14033},
    "Harborside Resort at Atlantis": {"retail_per_night": 800, "brand": "Sheraton/Westin", "location": "Nassau, Bahamas", "tug_resort_id": 13826},
    "Marriott's Oceanwatch Villas": {"retail_per_night": 500, "brand": "Marriott", "location": "Myrtle Beach, SC", "tug_resort_id": 13896},
    "Marriott's Grande Vista": {"retail_per_night": 320, "brand": "Marriott", "location": "Orlando, FL", "tug_resort_id": 14025},
    "Disney's Saratoga Springs Resort": {"retail_per_night": 550, "brand": "Disney Vacation Club", "location": "Orlando, FL", "tug_resort_id": 13701},
    "Hilton Grand Vacations Club on the Las Vegas Strip": {"retail_per_night": 280, "brand": "Hilton", "location": "Las Vegas, NV", "tug_resort_id": 0},
    "Marriott's Timber Lodge": {"retail_per_night": 450, "brand": "Marriott", "location": "Lake Tahoe, CA", "tug_resort_id": 13880},
    "Grand Solmar Land's End": {"retail_per_night": 700, "brand": "Solmar", "location": "Cabo San Lucas, Mexico", "tug_resort_id": 14913},
    "Ritz-Carlton Club, St. Thomas": {"retail_per_night": 1200, "brand": "Ritz-Carlton", "location": "St. Thomas, USVI", "tug_resort_id": 14884},
    "Ritz-Carlton Club, Aspen Highlands": {"retail_per_night": 1400, "brand": "Ritz-Carlton", "location": "Aspen, CO", "tug_resort_id": 15186},
    "Ritz-Carlton Club, Vail": {"retail_per_night": 1300, "brand": "Ritz-Carlton", "location": "Vail, CO", "tug_resort_id": 14975},
    "Ritz-Carlton Club, Lake Tahoe": {"retail_per_night": 1200, "brand": "Ritz-Carlton", "location": "Lake Tahoe, CA", "tug_resort_id": 15304},
    "Ritz-Carlton Club, San Francisco": {"retail_per_night": 900, "brand": "Ritz-Carlton", "location": "San Francisco, CA", "tug_resort_id": 15326},
    "Four Seasons Residence Club Aviara": {"retail_per_night": 850, "brand": "Four Seasons", "location": "Carlsbad, CA", "tug_resort_id": 14544},
    "Four Seasons Residence Club Scottsdale": {"retail_per_night": 950, "brand": "Four Seasons", "location": "Scottsdale, AZ", "tug_resort_id": 14552},
    "Four Seasons Residence Club Jackson Hole": {"retail_per_night": 1300, "brand": "Four Seasons", "location": "Jackson Hole, WY", "tug_resort_id": 14816},
    "Grand Luxxe at Vidanta Riviera Maya": {"retail_per_night": 750, "brand": "Grand Luxxe", "location": "Riviera Maya, Mexico", "tug_resort_id": 14964},
    "Casa Velas Boutique Hotel": {"retail_per_night": 650, "brand": "Casa Velas", "location": "Puerto Vallarta, Mexico", "tug_resort_id": 14742},
    "Club Velas Vallarta": {"retail_per_night": 600, "brand": "Independent", "location": "Puerto Vallarta, Mexico", "tug_resort_id": 14516},
    "Park Hyatt Beaver Creek": {"retail_per_night": 900, "brand": "Park Hyatt", "location": "Beaver Creek, CO", "tug_resort_id": 15028},
    "Hyatt Vacation Club Ka'anapali Beach": {"retail_per_night": 800, "brand": "Hyatt Vacation Club", "location": "Maui, HI", "tug_resort_id": 15094},
    "Hyatt Vacation Club at Northstar Lodge": {"retail_per_night": 750, "brand": "Hyatt Vacation Club", "location": "Lake Tahoe, CA", "tug_resort_id": 14896},
    "Hyatt Sunset Harbor Resort": {"retail_per_night": 700, "brand": "Hyatt Vacation Club", "location": "Key West, FL", "tug_resort_id": 13833},
    "Hyatt Windward Pointe Resort": {"retail_per_night": 600, "brand": "Hyatt Vacation Club", "location": "Key West, FL", "tug_resort_id": 13850},
    "Westin Nanea Ocean Villas": {"retail_per_night": 850, "brand": "Westin", "location": "Maui, HI", "tug_resort_id": 15165},
    "Westin Kierland Villas": {"retail_per_night": 650, "brand": "Westin", "location": "Scottsdale, AZ", "tug_resort_id": 14466},
    "Marriott Waiohai Beach Club": {"retail_per_night": 650, "brand": "Marriott", "location": "Kauai, HI", "tug_resort_id": 13998},
    "Marriott Kauai Lagoons Kalanipu'u": {"retail_per_night": 700, "brand": "Marriott", "location": "Kauai, HI", "tug_resort_id": 14918},
    "Marriott Lakeshore Reserve": {"retail_per_night": 500, "brand": "Marriott", "location": "Orlando, FL", "tug_resort_id": 14853},
    "Hilton Club La Pacifica Los Cabos": {"retail_per_night": 600, "brand": "Hilton", "location": "Los Cabos, Mexico", "tug_resort_id": 15338},
}

DEFAULT_RETAIL_BENCHMARK = 350

# Bedroom multipliers to adjust base retail rates dynamically by unit size
BEDROOM_MULTIPLIERS = {
    0: 0.70,  # Studio / 0 Bedroom
    1: 1.00,  # 1 Bedroom (Base retail benchmark)
    2: 1.45,  # 2 Bedroom
    3: 1.95,  # 3+ Bedroom
}

def get_retail_rate_for_unit(base_retail: float, unit_type: str) -> float:
    """
    Returns the dynamically scaled retail rate per night based on the unit type/bedroom count.
    """
    if re.search(r'studio', unit_type, re.IGNORECASE):
        beds = 0
    else:
        m = re.search(r'(\d+)\s*bed', unit_type, re.IGNORECASE)
        beds = int(m.group(1)) if m else 1
        
    multiplier = BEDROOM_MULTIPLIERS.get(beds, 1.95 if beds >= 3 else 1.0)
    return base_retail * multiplier

# ─────────────────────────────────────────────────────────────────────────────

def calculate_deal_score(listing_price: float, duration_days: int, retail_per_night: float, brand: str) -> Dict[str, Any]:
    """
    Calculates detailed value metrics and deal scores.
    """
    total_retail = retail_per_night * duration_days
    price_per_night = listing_price / duration_days
    
    # Calculate savings
    total_savings = total_retail - listing_price
    savings_pct = (total_savings / total_retail) * 100
    
    # Core deal score calculation (0 - 100 scale)
    # 50% savings is a baseline good score (80/100)
    base_score = 30 + (savings_pct * 1.0)
    
    # Brand premium boosts
    brand_boost = 0
    if brand in ["Ritz-Carlton", "Four Seasons", "Park Hyatt", "Grand Luxxe"]:
        brand_boost = 10
    elif brand in ["Disney Vacation Club", "Westin", "Marriott", "Hyatt Vacation Club", "Casa Velas", "Hilton"]:
        brand_boost = 5
        
    final_score = min(max(base_score + brand_boost, 0.0), 100.0)
    
    # Grade assignment
    if savings_pct >= 60:
        grade = "A+"
        deal_class = "super-deal"
    elif savings_pct >= 45:
        grade = "A"
        deal_class = "great-deal"
    elif savings_pct >= 30:
        grade = "B"
        deal_class = "good-deal"
    else:
        grade = "C"
        deal_class = "fair-deal"
        
    return {
        "retail_per_night": round(retail_per_night, 2),
        "total_retail": round(total_retail, 2),
        "price_per_night": round(price_per_night, 2),
        "total_savings": round(total_savings, 2),
        "savings_pct": round(savings_pct, 1),
        "score": round(final_score, 1),
        "grade": grade,
        "class": deal_class
    }

def parse_price(price_str: str) -> float:
    """Parse a price string like '$3,895.00' into a float."""
    try:
        return float(re.sub(r'[^\d.]', '', price_str))
    except:
        return 0.0


def parse_nights_from_dates(date_str: str) -> int:
    """
    Estimate nights from a date range string like 'Jan 01, 2026 - Dec 24, 2026'.
    Falls back to 7 if parsing fails.
    """
    try:
        parts = [p.strip() for p in date_str.split(' - ')]
        if len(parts) == 2:
            fmt = "%b %d, %Y"
            start = datetime.strptime(parts[0], fmt)
            end = datetime.strptime(parts[1], fmt)
            nights = (end - start).days
            # Cap to a reasonable single-stay range (1–21 nights)
            if 1 <= nights <= 21:
                return nights
    except:
        pass
    return 7


def scrape_resort_listings(resort_name: str, benchmark: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scrapes live rental listings for a specific resort from TUG Marketplace via POST.
    Extracts real direct links in the format:
      https://tug2.com/resorts/resort/{slug}/classified-listing/{id}
    """
    if not BeautifulSoup:
        return []

    resort_id = benchmark.get("tug_resort_id", 0)
    if not resort_id:
        return []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://tug2.com/timesharemarketplace/search',
    }
    post_data = {
        'ResortId': str(resort_id),
        'ForRent': 'true',
        'Submit': 'Show Results',
    }

    try:
        r = requests.post(
            'https://tug2.com/timesharemarketplace/search',
            headers=headers,
            data=post_data,
            timeout=20,
        )
        if r.status_code != 200:
            print(f"  [{resort_name}] HTTP {r.status_code} — skipping")
            return []

        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.find_all('div', class_='listing-row')
        print(f"  [{resort_name}] Found {len(rows)} live listings")

        parsed = []
        for row in rows:
            # --- Extract the direct listing link ---
            link_tag = row.find('a', href=lambda h: h and 'classified-listing' in h)
            if not link_tag:
                continue
            full_link = "https://tug2.com" + link_tag['href']

            # Extract listing ID from URL path
            m = re.search(r'/classified-listing/(\d+)', link_tag['href'])
            listing_id = f"TUG-{m.group(1)}" if m else "TUG-LIVE"

            # --- Extract description / notes ---
            desc_el = row.find('small')
            notes = desc_el.get_text(strip=True) if desc_el else ""

            # Walk through child divs and look for recognisable content
            all_divs = row.find_all('div', class_=lambda c: c and 'col-xs-12' in c)
            date_str = ""
            price_str = ""
            unit_str = ""
            sleeps_str = ""

            for div in all_divs:
                text = div.get_text(separator=' ', strip=True)
                if re.search(r'\w{3}\s+\d+,\s*\d{4}.*-.*\w{3}\s+\d+,\s*\d{4}', text):
                    date_str = text
                elif re.search(r'\$[\d,]+', text):
                    price_str = text
                elif re.search(r'bed|studio|sleeps', text, re.IGNORECASE):
                    unit_str = text
                    sleeps_match = re.search(r'sleeps\s*(\d+)', text, re.IGNORECASE)
                    if sleeps_match:
                        sleeps_str = sleeps_match.group(1)

            # Parse price
            price_match = re.search(r'\$([\d,]+(?:\.\d{2})?)', price_str)
            listing_price = parse_price(price_match.group(0)) if price_match else 0.0
            if listing_price <= 0:
                continue

            # Parse nights from date range
            nights = parse_nights_from_dates(date_str)

            # Parse bedrooms
            if re.search(r'studio', unit_str, re.IGNORECASE):
                unit_type = "Studio"
                beds = 0
            else:
                bed_match = re.search(r'(\d+)\s*bed', unit_str, re.IGNORECASE)
                beds = int(bed_match.group(1)) if bed_match else 1
                unit_type = f"{beds} Bedroom"
            if sleeps_str:
                unit_type += f" (sleeps {sleeps_str})"

            # Parse check-in date (start of the date range)
            check_in = datetime.now().strftime("%Y-%m-%d")
            try:
                date_parts = [p.strip() for p in date_str.split(' - ')]
                if date_parts:
                    check_in = datetime.strptime(date_parts[0].strip(), "%b %d, %Y").strftime("%Y-%m-%d")
            except:
                pass

            # Calculate deal score with bedroom-adjusted retail rate
            dynamic_retail = get_retail_rate_for_unit(benchmark["retail_per_night"], unit_type)
            metrics = calculate_deal_score(
                listing_price, nights,
                dynamic_retail,
                benchmark["brand"]
            )

            # Apply user constraints: max $400/night per bedroom, min 30% savings
            num_bedrooms = max(beds, 1)
            price_per_night = listing_price / nights
            price_per_night_per_br = price_per_night / num_bedrooms

            if price_per_night_per_br > 400.0:
                continue
            if metrics["savings_pct"] < 30.0:
                continue

            listing = {
                "resort": resort_name,
                "unit_type": unit_type,
                "view": "Standard View",
                "check_in": check_in,
                "nights": nights,
                "listing_price": listing_price,
                "listing_id": listing_id,
                "platform": "TUG Live",
                "link": full_link,
                "owner": "TUG Member",
                "notes": notes or f"Live rental listing at {resort_name}.",
                "location": benchmark["location"],
                "brand": benchmark["brand"],
            }
            listing.update(metrics)
            parsed.append(listing)

        return parsed

    except Exception as e:
        print(f"  [{resort_name}] Scrape error: {e}")
        return []


def get_high_fidelity_listings() -> List[Dict[str, Any]]:
    """
    Fallback: returns high-fidelity simulated listings if live scraping fails.
    Uses the ResortId-based search URL as the link so it still navigates to
    real filtered results on TUG.
    """
    today = datetime.now()
    fallback_templates = [
        {"resort": "Ritz-Carlton Club, St. Thomas",         "unit_type": "2 Bedroom Residence",  "nights": 7, "listing_price": 3800.0},
        {"resort": "Four Seasons Residence Club Aviara",     "unit_type": "1 Bedroom Villa",      "nights": 7, "listing_price": 2200.0},
        {"resort": "Westin Kaanapali Ocean Resort Villas", "unit_type": "2 Bedroom (Lockoff)", "nights": 7, "listing_price": 2400.0},
        {"resort": "Marriott's Maui Ocean Club",            "unit_type": "1 Bedroom Suite",     "nights": 7, "listing_price": 2100.0},
        {"resort": "Disney's Aulani Resort & Spa",          "unit_type": "2 Bedroom Villa",      "nights": 6, "listing_price": 2900.0},
        {"resort": "Harborside Resort at Atlantis",         "unit_type": "2 Bedroom Deluxe",     "nights": 7, "listing_price": 2200.0},
        {"resort": "Marriott's Grande Vista",               "unit_type": "2 Bedroom Villa",      "nights": 7, "listing_price": 850.0},
        {"resort": "Marriott's Timber Lodge",               "unit_type": "1 Bedroom Villa",      "nights": 7, "listing_price": 1400.0},
        {"resort": "Marriott's Ko Olina Beach Club",        "unit_type": "2 Bedroom Beachfront", "nights": 7, "listing_price": 2450.0},
        {"resort": "Grand Solmar Land's End",               "unit_type": "Presidential Suite",   "nights": 7, "listing_price": 2100.0},
    ]
    listings = []
    for i, t in enumerate(fallback_templates):
        benchmark = RESORT_RETAIL_BENCHMARKS.get(t["resort"], {
            "retail_per_night": DEFAULT_RETAIL_BENCHMARK,
            "brand": "Independent",
            "location": "Varies",
            "tug_resort_id": 0,
        })
        resort_id = benchmark.get("tug_resort_id", 0)
        link = (f"https://tug2.com/timesharemarketplace/search?ResortId={resort_id}&ForRent=True"
                if resort_id else "https://tug2.com/timesharemarketplace/rentals")
        base_retail = benchmark.get("retail_per_night", DEFAULT_RETAIL_BENCHMARK)
        dynamic_retail = get_retail_rate_for_unit(base_retail, t["unit_type"])
        metrics = calculate_deal_score(t["listing_price"], t["nights"], dynamic_retail, benchmark["brand"])

        # Determine bedroom count for fallback templates
        if re.search(r'studio', t["unit_type"], re.IGNORECASE):
            beds = 0
        else:
            m = re.search(r'(\d+)\s*bed', t["unit_type"], re.IGNORECASE)
            beds = int(m.group(1)) if m else 1

        num_bedrooms = max(beds, 1)
        price_per_night = t["listing_price"] / t["nights"]
        price_per_night_per_br = price_per_night / num_bedrooms

        if price_per_night_per_br > 400.0 or metrics["savings_pct"] < 30.0:
            continue

        listings.append({
            **t,
            "view": "Standard View",
            "check_in": (today + timedelta(days=30 + i*10)).strftime("%Y-%m-%d"),
            "listing_id": f"FALLBACK-{i+1}",
            "platform": "TUG (Fallback)",
            "link": link,
            "owner": "TUG Member",
            "notes": f"Search live rentals for this resort on TUG Marketplace.",
            "location": benchmark["location"],
            "brand": benchmark["brand"],
            **metrics,
        })
    listings.sort(key=lambda x: x["score"], reverse=True)
    return listings

def scrape_all_resorts() -> List[Dict[str, Any]]:
    """
    Loops through all resorts in RESORT_RETAIL_BENCHMARKS, scrapes their live
    listings from TUG, and returns the aggregated list.
    """
    all_listings = []
    print("Starting live scrape for all resorts...")
    for resort_name, benchmark in RESORT_RETAIL_BENCHMARKS.items():
        if benchmark.get("tug_resort_id"):
            try:
                listings = scrape_resort_listings(resort_name, benchmark)
                if listings:
                    all_listings.extend(listings)
                # Respectful rate limiting: wait between 1 to 2 seconds
                time.sleep(random.uniform(1.0, 2.0))
            except Exception as e:
                print(f"Error scraping {resort_name}: {e}")
    return all_listings


def main():
    print(f"\n{'='*60}\nTimeshare Rental Deal Scanner Engine — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{'='*60}\n")

    # Scrape live listings from TUG for all tracked resorts via POST
    # Each card links directly to: /resorts/resort/{slug}/classified-listing/{id}
    all_deals = scrape_all_resorts()

    if not all_deals:
        print("⚠️  No live listings scraped — falling back to high-fidelity templates.")
        all_deals = get_high_fidelity_listings()
    else:
        print(f"\n✅ Scraped {len(all_deals)} live listings across all resorts.")

    # Sort by deal score descending
    all_deals.sort(key=lambda x: x["score"], reverse=True)

    # Export to deals.json in the web folder
    try:
        with open(DEALS_JSON_PATH, "w") as f:
            json.dump(all_deals, f, indent=2)
        print(f"✅ Exported {len(all_deals)} deals to {DEALS_JSON_PATH}")
    except Exception as e:
        print(f"❌ Failed to export JSON: {e}")


if __name__ == "__main__":
    main()

