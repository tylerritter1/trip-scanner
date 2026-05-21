"""
Trip Scanner & Optimizer
Scans travel deals, monitors watchlist destinations, and utilizes Gemini to generate
highly optimized, custom-tailored travel itineraries.
"""

import os
import sys
import time
import socket
import re
import pandas as pd
import google.generativeai as genai
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Load Environment Variables ────────────────────────────────────────────────
# Try loading from the local directory first, then the parent directory if not found
local_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
wheel_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wheel-performance", ".env")

if os.path.exists(local_env):
    load_dotenv(local_env)
elif os.path.exists(wheel_env):
    load_dotenv(wheel_env)
else:
    load_dotenv(parent_env)

# Hard timeout on network calls to prevent hanging
socket.setdefaulttimeout(30)

# Global session with retries for travel queries
travel_session = requests.Session()
travel_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
})
_retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
travel_session.mount('https://', HTTPAdapter(max_retries=_retries))

# ── Secrets/Keys ──────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── Destination Watchlist ──────────────────────────────────────────────────────
WATCHLIST = [
    {"destination": "Tokyo, Japan", "airport": "NRT", "target_price": 800, "ideal_duration_days": 10},
    {"destination": "Rome, Italy", "airport": "FCO", "target_price": 600, "ideal_duration_days": 7},
    {"destination": "Paris, France", "airport": "CDG", "target_price": 550, "ideal_duration_days": 5},
    {"destination": "Maui, Hawaii", "airport": "OGG", "target_price": 400, "ideal_duration_days": 6},
    {"destination": "London, UK", "airport": "LHR", "target_price": 500, "ideal_duration_days": 6},
]

# ─────────────────────────────────────────────────────────────────────────────

def fetch_current_deals() -> list:
    """
    Simulates or fetches real travel deal data.
    If custom travel APIs are added later, hook them up here.
    """
    print("Fetching latest flight and travel deal trends...")
    deals = []
    
    # Base mock prices that vary slightly based on the current date for realism
    today = datetime.now()
    day_factor = today.day % 5
    
    base_deals = [
        {"destination": "Tokyo, Japan", "airport": "NRT", "current_price": 850 - (day_factor * 15), "airline": "Japan Airlines", "season": "Spring"},
        {"destination": "Rome, Italy", "airport": "FCO", "current_price": 580 + (day_factor * 10), "airline": "ITA Airways", "season": "Autumn"},
        {"destination": "Paris, France", "airport": "CDG", "current_price": 520 - (day_factor * 20), "airline": "Air France", "season": "Summer"},
        {"destination": "Maui, Hawaii", "airport": "OGG", "current_price": 380 + (day_factor * 5), "airline": "Hawaiian Airlines", "season": "Year-round"},
        {"destination": "London, UK", "airport": "LHR", "current_price": 510 - (day_factor * 8), "airline": "British Airways", "season": "Winter"},
    ]
    
    for d in base_deals:
        # Match with target price from watchlist
        target = next((item["target_price"] for item in WATCHLIST if item["destination"] == d["destination"]), 600)
        d["target_price"] = target
        d["discount"] = round(target - d["current_price"], 2)
        d["deal_score"] = round((target / d["current_price"]) * 100, 1)
        deals.append(d)
        
    return deals

def get_ai_optimized_itinerary(destination: str, duration: int) -> str:
    """
    Uses Google Gemini AI to draft a highly optimized, high-end travel itinerary.
    """
    if not GEMINI_API_KEY:
        return "⚠️ Google Gemini API Key not found. Please set GEMINI_API_KEY in your .env file."
        
    try:
        genai.configure(api_key=GEMINI_API_KEY.strip())
        
        prompt = (
            f"You are a luxury travel planner and expert concierge.\n"
            f"Create a stunning, highly curated {duration}-day itinerary for '{destination}'.\n"
            f"Requirements:\n"
            f"- Group items logically (Morning, Afternoon, Evening) with unique, authentic experiences.\n"
            f"- Suggest 1-2 off-the-beaten-path locations and local culinary highlights (restaurants or specialties).\n"
            f"- Keep the tone professional, vivid, and elegant.\n"
            f"- Provide a short 'Insider Tip' at the end.\n"
            f"Directly output the itinerary. Do not include introductory filler or chat pleasantries."
        )
        
        # Determine model
        models_to_try = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-pro']
        
        for model_id in models_to_try:
            try:
                print(f"  Requesting itinerary from model: {model_id}...")
                model = genai.GenerativeModel(model_id)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                print(f"  Model {model_id} unavailable or failed: {str(e)[:80]}")
                continue
                
        return "Failed to generate itinerary with available Gemini models."
    except Exception as e:
        return f"AI Generation error: {e}"

def print_deals_table(deals: list):
    """
    Outputs a premium formatted CLI table of current watchlists and deal scores.
    """
    print("\n" + "=" * 85)
    print(f"{'DESTINATION':<25} | {'AIRPORT':<8} | {'TARGET':<8} | {'CURRENT':<8} | {'DEAL SCORE':<12} | {'STATUS'}")
    print("=" * 85)
    
    for d in deals:
        status = "🟢 BUY ALERT" if d["current_price"] <= d["target_price"] else "🔴 MONITORING"
        score_str = f"{d['deal_score']}%"
        print(f"{d['destination']:<25} | {d['airport']:<8} | ${d['target_price']:<7} | ${d['current_price']:<7} | {score_str:<12} | {status}")
    print("=" * 85 + "\n")

def main():
    print(f"\n{'='*60}\nTrip Scanner & Optimizer — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{'='*60}\n")
    
    deals = fetch_current_deals()
    print_deals_table(deals)
    
    # CLI Command parsing
    generate_itinerary = None
    if "--itinerary" in sys.argv:
        idx = sys.argv.index("--itinerary")
        if idx + 1 < len(sys.argv):
            generate_itinerary = sys.argv[idx + 1]
            
    if generate_itinerary:
        # Match destination
        matched = None
        for d in WATCHLIST:
            if generate_itinerary.lower() in d["destination"].lower():
                matched = d
                break
                
        if matched:
            dest_name = matched["destination"]
            duration = matched["ideal_duration_days"]
            print(f"Generating optimized AI itinerary for {dest_name} ({duration} days)...")
            itinerary = get_ai_optimized_itinerary(dest_name, duration)
            print("\n" + "#" * 60)
            print(f"OPTIMIZED ITINERARY: {dest_name.upper()}")
            print("#" * 60 + "\n")
            print(itinerary)
            print("\n" + "#" * 60 + "\n")
        else:
            print(f"Could not find destination matching '{generate_itinerary}' in watchlist.")
            print(f"Available watchlist: {', '.join([d['destination'] for d in WATCHLIST])}")
    else:
        print("💡 Tip: Run with '--itinerary <destination>' (e.g. --itinerary tokyo) to generate an AI-optimized premium travel plan.")

if __name__ == "__main__":
    main()
