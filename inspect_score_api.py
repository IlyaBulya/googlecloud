#!/usr/bin/env python3
"""Test NHL score endpoint structure."""

import requests
import json

date = "2025-01-15"
url = f"https://api-web.nhle.com/v1/score/{date}"
print(f"Testing {url}\n")

r = requests.get(url, timeout=30)
print(f"HTTP Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"Response keys: {list(data.keys())}")
    
    games = data.get("games", [])
    print(f"Number of games: {len(games)}")
    
    if games:
        game = games[0]
        print(f"\n=== First game structure ===")
        print(f"Top-level keys: {list(game.keys())}\n")
        
        print(f"game['id']: {game.get('id')}")
        print(f"game['gameDate']: {game.get('gameDate')}")
        print(f"game['gameState']: {game.get('gameState')}")
        print(f"game['season']: {game.get('season')}")
        print(f"game['gameType']: {game.get('gameType')}")
        print(f"game['startTimeUTC']: {game.get('startTimeUTC')}")
        print(f"game['venue']: {game.get('venue')}")
        
        home = game.get('homeTeam', {})
        away = game.get('awayTeam', {})
        
        print(f"\nhomeTeam keys: {list(home.keys())}")
        print(f"  abbrev: {home.get('abbrev')}")
        print(f"  score: {home.get('score')}")
        print(f"  commonName: {home.get('commonName')}")
        print(f"  placeName: {home.get('placeName')}")
        
        print(f"\nawayTeam keys: {list(away.keys())}")
        print(f"  abbrev: {away.get('abbrev')}")
        print(f"  score: {away.get('score')}")
        print(f"  commonName: {away.get('commonName')}")
        print(f"  placeName: {away.get('placeName')}")
        
        print(f"\n=== Full first game ===")
        print(json.dumps(game, indent=2)[:1500])
else:
    print(f"Error: {r.text[:500]}")
