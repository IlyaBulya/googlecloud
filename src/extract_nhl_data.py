import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from src.utils import date_range, ensure_directory, safe_get

BASE_URL = "https://api-web.nhle.com/v1"


def fetch_json(url: str) -> dict:
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"Warning: failed to fetch {url}: {exc}")
        return {}


def parse_game(schedule_game: dict, score_game: dict | None, source_date: str, ingested_at: str) -> dict:
    game_id = safe_get(schedule_game, "gamePk")
    home_team = schedule_game.get("teams", {}).get("home", {}).get("team", {})
    away_team = schedule_game.get("teams", {}).get("away", {}).get("team", {})
    home_score = safe_get(score_game or {}, "teams", "home", "score", default=0)
    away_score = safe_get(score_game or {}, "teams", "away", "score", default=0)
    return {
        "game_id": game_id,
        "game_date": source_date,
        "season": safe_get(schedule_game, "season"),
        "game_type": safe_get(schedule_game, "gameType"),
        "venue": safe_get(schedule_game, "venue", "name"),
        "home_team_abbrev": safe_get(home_team, "abbreviation"),
        "away_team_abbrev": safe_get(away_team, "abbreviation"),
        "home_team_name": safe_get(home_team, "name"),
        "away_team_name": safe_get(away_team, "name"),
        "home_score": home_score if isinstance(home_score, int) else int(home_score or 0),
        "away_score": away_score if isinstance(away_score, int) else int(away_score or 0),
        "game_state": safe_get(score_game or schedule_game, "status", "detailedState"),
        "start_time_utc": safe_get(schedule_game, "gameDate"),
        "source_date": source_date,
        "ingested_at": ingested_at,
    }


def extract_nhl_data(start_date: str, end_date: str, output_dir: str = "data/raw") -> tuple[str, int]:
    ensure_directory(output_dir)
    extracted_records: list[dict] = []
    ingested_at = datetime.now(timezone.utc).isoformat()

    for current_date in date_range(start_date, end_date):
        print(f"Extracting NHL data for {current_date}")
        schedule_response = fetch_json(f"{BASE_URL}/schedule/{current_date}")
        score_response = fetch_json(f"{BASE_URL}/score/{current_date}")

        schedule_games = []
        for date_block in schedule_response.get("dates", []):
            schedule_games.extend(date_block.get("games", []))

        score_games = {}
        for date_block in score_response.get("dates", []):
            for game in date_block.get("games", []):
                game_pk = safe_get(game, "gamePk")
                if game_pk is not None:
                    score_games[game_pk] = game

        if not schedule_games:
            print(f"No games found for {current_date}. Continuing to next date.")
            continue

        for schedule_game in schedule_games:
            game_id = safe_get(schedule_game, "gamePk")
            score_game = score_games.get(game_id)
            record = parse_game(schedule_game, score_game, source_date=current_date, ingested_at=ingested_at)
            extracted_records.append(record)

    local_filename = f"nhl_games_{start_date}_{end_date}.jsonl"
    output_path = str(Path(output_dir) / local_filename)

    if extracted_records:
        df = pd.DataFrame(extracted_records)
        df.to_json(output_path, orient="records", lines=True, date_format="iso")
    else:
        print("No records extracted. Writing an empty JSONL file.")
        Path(output_path).write_text("")

    print(f"Extracted {len(extracted_records)} rows to {output_path}")
    return output_path, len(extracted_records)
