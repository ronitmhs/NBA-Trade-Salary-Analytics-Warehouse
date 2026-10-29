from pathlib import Path
import time

import duckdb
import pandas as pd


RAW_DATA_DIR = Path("data/raw")
START_SEASON = 2010
END_SEASON = 2026
MAX_RETRIES = 3
REQUEST_DELAY = 1

BASE_URL = (
    "https://basketball-data.billmill.org/"
    "nba/bbref/bbref_salaries"
)


def salary_url(season: int) -> str:
    """Build the Parquet URL for one salary season."""
    return f"{BASE_URL}/season={season}/data.parquet"


def extract_salaries(season: int) -> pd.DataFrame:
    """Extract NBA salary data for one season."""
    connection = duckdb.connect()

    try:
        url = salary_url(season)

        query = f"""
            SELECT
                season,
                team_id,
                bbref_id,
                player_id,
                salary
            FROM read_parquet('{url}')
        """

        return connection.execute(query).fetchdf()

    finally:
        connection.close()


def save_salaries(df: pd.DataFrame, season: int) -> Path:
    """Save raw salary data locally."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RAW_DATA_DIR / f"salaries_{season}.csv"
    df.to_csv(output_path, index=False)

    return output_path


def extract_season_with_retry(season: int) -> bool:
    """Extract one salary season with retry handling."""
    output_path = RAW_DATA_DIR / f"salaries_{season}.csv"

    if output_path.exists():
        print(f"[SKIP] {season} already exists")
        return True

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[EXTRACT] {season} - attempt {attempt}")

            df = extract_salaries(season)

            if df.empty:
                raise ValueError(f"No salary data returned for {season}")

            save_salaries(df, season)

            mapped_players = df["player_id"].notna().sum()

            print(
                f"[SUCCESS] {season}: "
                f"{len(df):,} salary rows | "
                f"{mapped_players:,} NBA player IDs"
            )

            return True

        except Exception as error:
            print(f"[ERROR] {season}: {error}")

            if attempt < MAX_RETRIES:
                wait_time = attempt * 5
                print(f"[RETRY] Waiting {wait_time} seconds...")
                time.sleep(wait_time)

    print(f"[FAILED] {season}")
    return False


def main() -> None:
    seasons = range(START_SEASON, END_SEASON + 1)

    successful = []
    failed = []

    print(
        f"Starting salary extraction for "
        f"{START_SEASON} through {END_SEASON}\n"
    )

    for season in seasons:
        success = extract_season_with_retry(season)

        if success:
            successful.append(season)
        else:
            failed.append(season)

        time.sleep(REQUEST_DELAY)

    print("\nExtraction complete.")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print(f"Failed seasons: {failed}")


if __name__ == "__main__":
    main()