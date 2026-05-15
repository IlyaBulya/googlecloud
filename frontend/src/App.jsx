import { useEffect, useState } from "react";

function SummaryCard({ label, value }) {
  return (
    <div className="card small-card">
      <div className="card-label">{label}</div>
      <div className="card-value">{value}</div>
    </div>
  );
}

function ProbabilityBar({ home, away }) {
  const homeWidth = Math.round(home * 100);
  const awayWidth = Math.round(away * 100);
  return (
    <div className="probability-bar">
      <div className="probability-segment home" style={{ width: `${homeWidth}%` }}>
        <span>{homeWidth}%</span>
      </div>
      <div className="probability-segment away" style={{ width: `${awayWidth}%` }}>
        <span>{awayWidth}%</span>
      </div>
    </div>
  );
}

function StatBlock({ title, value }) {
  return (
    <div className="stat-block">
      <div className="stat-title">{title}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function TeamMetricsColumn({ teamLabel, stats }) {
  return (
    <div className="team-column">
      <div className="team-column-title">{teamLabel}</div>
      <StatBlock title="Win rate" value={`${(stats.overall_win_rate * 100).toFixed(0)}%`} />
      <StatBlock title="Split win rate" value={`${(stats.home_or_away_win_rate * 100).toFixed(0)}%`} />
      <StatBlock title="Avg goals for" value={stats.avg_goals_for} />
      <StatBlock title="Avg goals against" value={stats.avg_goals_against} />
      <StatBlock title="Games played" value={stats.games_played} />
    </div>
  );
}

function GameCard({ game }) {
  const homeProb = game.home_probability;
  const awayProb = game.away_probability;

  return (
    <div className="card game-card">
      <div className="game-header">
        <div className="game-title">
          <strong>{game.away_team_abbrev}</strong> @ <strong>{game.home_team_abbrev}</strong>
        </div>
        <div className="game-time">{game.start_time_utc || "TBA"}</div>
      </div>

      <div className="game-summary">
        <div>
          <div className="small-label">Predicted winner</div>
          <div className="value-text">{game.predicted_winner_name || game.predicted_winner}</div>
        </div>
        <div>
          <div className="small-label">Confidence</div>
          <div className="value-text">{(game.confidence * 100).toFixed(0)}%</div>
        </div>
      </div>

      <ProbabilityBar home={homeProb} away={awayProb} />

      <div className="team-metrics-grid">
        <TeamMetricsColumn
          teamLabel="Away team"
          stats={{
            overall_win_rate: game.away_overall_win_rate,
            home_or_away_win_rate: game.away_away_win_rate,
            avg_goals_for: game.away_avg_goals_for,
            avg_goals_against: game.away_avg_goals_against,
            games_played: game.away_games_played,
          }}
        />
        <TeamMetricsColumn
          teamLabel="Home team"
          stats={{
            overall_win_rate: game.home_overall_win_rate,
            home_or_away_win_rate: game.home_home_win_rate,
            avg_goals_for: game.home_avg_goals_for,
            avg_goals_against: game.home_avg_goals_against,
            games_played: game.home_games_played,
          }}
        />
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
        <SummaryCard label="Avg goals/game" value={forecast.summary.avg_goals_per_game} />
        <SummaryCard label="Home win rate" value={`${(forecast.summary.home_win_rate * 100).toFixed(0)}%`} />
        <SummaryCard label="Away win rate" value={`${(forecast.summary.away_win_rate * 100).toFixed(0)}%`} />
        <SummaryCard label="Best team" value={`${forecast.summary.best_team_by_win_rate} (${(forecast.summary.best_team_win_rate * 100).toFixed(0)}%)`} />
        <SummaryCard label="Top scoring team" value={`${forecast.summary.highest_scoring_team} (${forecast.summary.highest_scoring_team_avg_goals})`} />
      </section>

      <section className="games-list">
        {forecast.games.length > 0 ? (
          forecast.games.map((game) => <GameCard key={game.game_id} game={game} />)
        ) : (
          <p>No upcoming games available for {forecast.upcoming_date}.</p>
        )}
      </section>

      <section className="footer-text">
        <p>NHL API → GCS → BigQuery → Team Stats → Forecast JSON → React UI</p>
        <p>This is a simple baseline prediction model for educational purposes, not betting advice.</p>
      </section>
    </main>
  );
}
