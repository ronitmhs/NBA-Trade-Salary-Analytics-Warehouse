from pathlib import Path

from nba_api.stats.endpoints import leaguedashplayerstats


RAW_DATA_DIR = Path("data/raw")


def extract_player_stats(season: str):
    """Extract NBA regular-season player stats for one season."""
    response = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
        timeout=60,
    )

    return response.get_data_frames()[0]


def save_player_stats(df, season: str) -> None:
    """Save raw season stats locally."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"player_stats_{season.replace('-', '_')}.csv"
    output_path = RAW_DATA_DIR / filename

    df.to_csv(output_path, index=False)

    print(f"Saved {len(df):,} rows to {output_path}")


if __name__ == "__main__":
    season = "2025-26"

    print(f"Extracting {season} NBA player stats...")

    stats_df = extract_player_stats(season)
    stats_df.insert(0, "SEASON", season)

    print("\nFirst 5 rows:")
    print(stats_df.head())

    print("\nColumns:")
    print(stats_df.columns.tolist())

    print("\nDataset shape:")
    print(stats_df.shape)

    save_player_stats(stats_df, season)