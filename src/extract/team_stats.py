from pathlib import Path
import time

import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats
from requests.exceptions import RequestException


RAW_DATA_DIR = Path("data/raw")
START_YEAR = 2000
END_YEAR = 2025
MAX_RETRIES = 3
REQUEST_DELAY = 2


def generate_seasons(start_year: int, end_year: int) -> list[str]:
    """Generate NBA season strings such as 2000-01."""
    return [
        f"{year}-{str(year + 1)[-2:]}"
        for year in range(start_year, end_year + 1)
    ]


def extract_team_stats(season: str) -> pd.DataFrame:
    """Extract regular-season team stats for one NBA season."""
    response = leaguedashteamstats.LeagueDashTeamStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
        timeout=60,
    )

    df = response.get_data_frames()[0]
    df.insert(0, "SEASON", season)

    return df


def save_team_stats(df: pd.DataFrame, season: str) -> Path:
    """Save raw team statistics for one season."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"team_stats_{season.replace('-', '_')}.csv"
    output_path = RAW_DATA_DIR / filename

    df.to_csv(output_path, index=False)

    return output_path


def extract_season_with_retry(season: str) -> bool:
    """Extract one season with retry handling."""
    filename = f"team_stats_{season.replace('-', '_')}.csv"
    output_path = RAW_DATA_DIR / filename

    if output_path.exists():
        print(f"[SKIP] {season} already exists")
        return True

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[EXTRACT] {season} - attempt {attempt}")

            df = extract_team_stats(season)

            if df.empty:
                raise ValueError(f"No data returned for {season}")

            save_team_stats(df, season)

            print(
                f"[SUCCESS] {season}: "
                f"{len(df):,} teams, {len(df.columns)} columns"
            )

            return True

        except (RequestException, ValueError, TimeoutError) as error:
            print(f"[ERROR] {season}: {error}")

            if attempt < MAX_RETRIES:
                wait_time = attempt * 5
                print(f"[RETRY] Waiting {wait_time} seconds...")
                time.sleep(wait_time)

    print(f"[FAILED] {season}")
    return False


def main() -> None:
    seasons = generate_seasons(START_YEAR, END_YEAR)

    print(
        f"Starting team stats extraction for {len(seasons)} NBA seasons "
        f"({seasons[0]} through {seasons[-1]})\n"
    )

    successful = []
    failed = []

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
        print(f"Failed seasons: {', '.join(failed)}")


if __name__ == "__main__":
    main()