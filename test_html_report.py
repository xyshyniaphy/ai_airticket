#!/usr/bin/env python3
"""
Test script for the HTML report generation function
"""

import json
from datetime import datetime
from scraper import generate_report, load_airport_data

# Sample test data matching the expected format
test_flights = [
    {
        "provider_name": "Gotogate",
        "price": "86,344円",
        "trip_type": "片道",
        "airline": "シンガポール航空",
        "flight_code": "SQ636, SQ468",
        "departure": {
            "date": "2025年12月27日",
            "time": "15:30",
            "airport": "NRT"
        },
        "arrival": {
            "date": "2025年12月28日",
            "time": "23:40",
            "airport": "CMB"
        },
        "duration": "35時間40分",
        "transfers": {
            "count_str": "乗継3回/自己",
            "airports": ["SIN", "KUL", "BKK"]
        },
        "plane_model": "ボーイング777",
        "baggage": ["手荷物1個無料", "受託荷物23kg無料"],
        "source_url": "https://www.tour.ne.jp/w_air/list/?air_type=0&slice_info=TYO-CMB#dpt_date=2025-12-27"
    },
    {
        "provider_name": "Gotogate",
        "price": "86,415円",
        "trip_type": "片道",
        "airline": "エミレーツ航空",
        "flight_code": "EK319, EK653",
        "departure": {
            "date": "2025年12月27日",
            "time": "19:50",
            "airport": "NRT"
        },
        "arrival": {
            "date": "2025年12月28日",
            "time": "23:40",
            "airport": "CMB"
        },
        "duration": "31時間20分",
        "transfers": {
            "count_str": "乗継4回/自己",
            "airports": ["DXB", "DOH", "KWI", "BAH"]
        },
        "plane_model": "エアバスA380",
        "baggage": ["手荷物1個無料", "受託荷物30kg無料"],
        "source_url": "https://www.tour.ne.jp/w_air/list/?air_type=0&slice_info=TYO-CMB#dpt_date=2025-12-27"
    },
    {
        "provider_name": "エクスペディア",
        "price": "99,828円",
        "trip_type": "片道",
        "airline": "キャセイパシフィック航空",
        "flight_code": "CX505, CX711",
        "departure": {
            "date": "2025年12月27日",
            "time": "21:00",
            "airport": "HND"
        },
        "arrival": {
            "date": "2025年12月28日",
            "time": "21:05",
            "airport": "CMB"
        },
        "duration": "27時間35分",
        "transfers": {
            "count_str": "乗継2回",
            "airports": ["HKG", "SIN"]
        },
        "plane_model": "ボーイング747",
        "baggage": ["手荷物1個無料", "受託荷物25kg無料"],
        "source_url": "https://www.tour.ne.jp/w_air/list/?air_type=0&slice_info=TYO-CMB#dpt_date=2025-12-27"
    }
]

# Test configuration
test_config = {
    "GEMINI_API_ENDPOINT": "https://generativelanguage.googleapis.com/v1beta",
    "GEMINI_API_KEY": "YOUR_API_KEY_HERE",
    "ORIGIN": "TYO",
    "DESTINATIONS": "CMB",
    "DEPARTURE_DATES": "20251227",
    "AIR_TYPE": "0",
    "USE_CACHE": "true",
    "TELEGRAM_BOT_TOKEN": "YOUR_BOT_TOKEN",
    "TELEGRAM_CHAT_ID": "YOUR_CHAT_ID"
}

def test_generate_report():
    """Test the HTML report generation function"""
    print("🧪 Testing HTML report generation...")
    
    # Load airport data
    airport_data = load_airport_data()
    
    print(f"Loaded airport data for {len(airport_data)} airports")
    print(f"Sample airports: {dict(list(airport_data.items())[:5])}")
    
    # Test the function
    try:
        generate_report(test_flights, test_config, airport_data)
        print("✅ Test completed successfully!")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generate_report()