# Trip Scanner ✈️🏨🚗

A standalone project designed to scan, log, and optimize trips, travel deals, or itineraries.

## Overview

`trip-scanner` is initialized as a flexible, standalone Python-based project. It is designed to collect travel data, scan for optimal flight/hotel pricing, or generate optimized itineraries using automated routines and Google Generative AI modules.

## Setup

1. **Environment Variables**:
   Create a `.env` file inside this directory and define any required keys:
   ```bash
   # Add your Google Gemini AI API Key
   GEMINI_API_KEY=your-api-key-here
   ```

2. **Dependencies**:
   Install dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main scanner script:
```bash
python3 trip_scanner.py
```

To generate a custom, high-end AI itinerary for a watchlist destination:
```bash
python3 trip_scanner.py --itinerary tokyo
```
