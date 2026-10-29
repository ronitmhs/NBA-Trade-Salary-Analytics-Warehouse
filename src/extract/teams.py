from pathlib import Path

import pandas as pd
from nba_api.stats.static import teams


RAW_DATA_DIR = Path("data/raw")


def extract_teams() -> pd.DataFrame:
    """Extract NBA team reference data."""
    team_data = teams.get_teams()
    return pd.DataFrame(team_data)


def save_teams(df: pd.DataFrame) -> Path:
    """Save raw NBA team reference data."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RAW_DATA_DIR / "teams.csv"
    df.to_csv(output_path, index=False)

    return output_path


def main() -> None:
    print("Extracting NBA team reference data...")

    teams_df = extract_teams()

    print("\nFirst 5 teams:")
    print(teams_df.head())

    print("\nColumns:")
    print(teams_df.columns.tolist())

    print("\nDataset shape:")
    print(teams_df.shape)

    output_path = save_teams(teams_df)

    print(f"\nSaved {len(teams_df):,} teams to {output_path}")


if __name__ == "__main__":
    main()