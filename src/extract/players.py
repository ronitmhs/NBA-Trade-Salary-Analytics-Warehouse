from pathlib import Path

import pandas as pd
from nba_api.stats.static import players


RAW_DATA_DIR = Path("data/raw")


def extract_players() -> pd.DataFrame:
    """Extract NBA player reference data."""
    player_data = players.get_players()
    return pd.DataFrame(player_data)


def save_players(df: pd.DataFrame) -> None:
    """Save raw player data locally."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RAW_DATA_DIR / "players.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved {len(df):,} players to {output_path}")


if __name__ == "__main__":
    players_df = extract_players()

    print("\nFirst 5 players:")
    print(players_df.head())

    print("\nColumns:")
    print(players_df.columns.tolist())

    print("\nDataset shape:")
    print(players_df.shape)

    save_players(players_df)