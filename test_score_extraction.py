#!/usr/bin/env python3
"""Test the updated score extraction."""

from src.extract_nhl_data import extract_nhl_data
import json

print("Testing extraction with /score endpoint...\n")
path, count = extract_nhl_data('2025-01-10', '2025-01-12')

print(f"\n=== First 3 records ===")
with open(path) as f:
    for i, line in enumerate(f):
        if i < 3:
            record = json.loads(line)
            print(f"\nRecord {i+1}:")
            print(f"  game_id: {record['game_id']}")
            print(f"  game_date: {record['game_date']}")
            print(f"  {record['home_team_abbrev']} {record['home_score']} vs {record['away_team_abbrev']} {record['away_score']}")
            print(f"  State: {record['game_state']}")

# Analyze scores
with open(path) as f:
    games_with_scores = 0
    games_without_scores = 0
    for line in f:
        record = json.loads(line)
        if record['home_score'] is not None and record['away_score'] is not None:
            games_with_scores += 1
        else:
            games_without_scores += 1

print(f"\n=== Statistics ===")
print(f"Total games extracted: {count}")
print(f"Games with scores: {games_with_scores}")
print(f"Games without scores: {games_without_scores}")
print(f"Score coverage: {100*games_with_scores/max(count,1):.1f}%")
