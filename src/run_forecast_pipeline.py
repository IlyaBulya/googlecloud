from src.config import load_forecast_config
from src.extract_upcoming_games import extract_upcoming_games
from src.generate_forecast import generate_forecast


def main() -> None:
    config = load_forecast_config()
    print("Starting NHL forecast pipeline")
    print(f"Upcoming date: {config.upcoming_date}")

    upcoming_path, upcoming_count = extract_upcoming_games(
        config.upcoming_date,
        output_dir="data/raw",
    )

    print(f"Upcoming games extracted: {upcoming_count}")
    print("If team_stats table does not exist, run: bq query --use_legacy_sql=false < sql/04_create_team_stats.sql")

    forecast_path = generate_forecast(config, upcoming_path)
    print("\nForecast generation complete")
    print(f"Forecast JSON: {forecast_path}")
    print(f"Forecasted games: {upcoming_count}")


if __name__ == "__main__":
    main()
