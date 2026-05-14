import { useEffect, useState } from "react";

function SummaryCard({ label, value }) {
  return (
    <div className="card small-card">
      <div className="card-label">{label}</div>
      <div className="card-value">{value}</div>
    </div>
  );
}

function GameCard({ game }) {
  return (
    <div className="card game-card">
      <div className="game-header">
        <div>
          <strong>{game.away_team_abbrev}</strong> @ <strong>{game.home_team_abbrev}</strong>
        </div>
        <div className="game-time">{game.start_time_utc || "TBA"}</div>
      </div>
      <div className="game-body">
        <div>{game.away_team_name || game.away_team_abbrev}</div>
        <div>{game.home_team_name || game.home_team_abbrev}</div>
      </div>
      <div className="game-footer">
        <span>Winner: {game.predicted_winner_name || game.predicted_winner}</span>
        <span>Confidence: {(game.confidence * 100).toFixed(0)}%</span>
        <span>Home: {(game.home_probability * 100).toFixed(0)}% | Away: {(game.away_probability * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
}

export default function App() {
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/data/forecast.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Unable to load forecast data");
        }
        return response.json();
      })
      .then(setForecast)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <main className="page-shell">
        <h1>NHL Match Forecast</h1>
        <p className="error">{error}</p>
      </main>
    );
  }

  if (!forecast) {
    return (
      <main className="page-shell">
        <h1>NHL Match Forecast</h1>
        <p>Loading forecast data...</p>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <header>
        <h1>NHL Match Forecast</h1>
        <p className="subtitle">GCP Data Engineering Pipeline Demo</p>
      </header>

      <section className="summary-grid">
        <SummaryCard label="Games analyzed" value={forecast.summary.games_analyzed} />
        <SummaryCard label="Teams analyzed" value={forecast.summary.teams_analyzed} />
        <SummaryCard label="Upcoming games" value={forecast.summary.upcoming_games} />
        <SummaryCard label="Avg goals per game" value={forecast.summary.avg_goals_per_game} />
      </section>

      <section className="games-list">
        {forecast.games.length > 0 ? (
          forecast.games.map((game) => <GameCard key={game.game_id} game={game} />)
        ) : (
          <p>No upcoming games available for {forecast.upcoming_date}.</p>
        )}
      </section>

      <section className="footer-text">
        <p>NHL API → GCS → BigQuery → Forecast JSON → UI</p>
        <p>This is a simple baseline prediction model for educational purposes, not betting advice.</p>
      </section>
    </main>
  );
}
