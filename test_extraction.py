#!/usr/bin/env python3
"""
Quick test to verify NHL API data extraction.
Run this locally before running the full pipeline.

Usage:
    python3 test_extraction.py --date 2025-05-14

"""

import argparse
from datetime import date
from src.extract_nhl_data import http_get_json_with_retry, BASE_URL

def test_schedule_endpoint(date_str: str) -> None:
    print(f"\n=== Testing /schedule/{date_str} ===")
    url = f"{BASE_URL}/schedule/{date_str}"
    print(f"URL: {url}")
    
    data = http_get_json_with_retry(url, timeout=30, retries=3, backoff_sec=1.0)
    
    if not data:
        print("ERROR: No response from NHL API")
        return
    
    print(f"Response keys: {data.keys()}")
    
    gameweek = data.get("gameWeek", [])
    print(f"Number of days in gameWeek: {len(gameweek)}")
    
    total_games = 0
    for day_block in gameweek:
        day_date = day_block.get("date")
        games = day_block.get("games", [])
        print(f"  Date: {day_date}, Games: {len(games)}")
        total_games += len(games)
        
        if games:
            first_game = games[0]
            print(f"    Sample game keys: {first_game.keys()}")
            print(f"    - homeTeam: {first_game.get('homeTeam', {}).get('abbrev')} vs awayTeam: {first_game.get('awayTeam', {}).get('abbrev')}")
            print(f"    - gameState: {first_game.get('gameState')}")
            print(f"    - score: {first_game.get('score')}")
            break
    
    print(f"Total games in response: {total_games}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test NHL API extraction")
    parser.add_argument("--date", help="YYYY-MM-DD to test (default: today)")
    args = parser.parse_args()
    
    test_date = args.date or date.today().isoformat()
    test_schedule_endpoint(test_date)
