from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw")


def salary_year_to_season(year: int) -> str:
    """Convert salary year 2026 to NBA season 2025-26."""
    start_year = year - 1
    return f"{start_year}-{str(year)[-2:]}"


def load_player_stats() -> pd.DataFrame:
    """Load all player-season statistics."""
    files = sorted(RAW_DATA_DIR.glob("player_stats_*.csv"))

    frames = []

    for file in files:
        df = pd.read_csv(
            file,
            usecols=["SEASON", "PLAYER_ID", "PLAYER_NAME"]
        )
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


def load_salaries() -> pd.DataFrame:
    """Load all salary records."""
    files = sorted(RAW_DATA_DIR.glob("salaries_*.csv"))

    frames = []

    for file in files:
        df = pd.read_csv(file)

        df["SEASON"] = df["season"].apply(
            lambda year: salary_year_to_season(int(year))
        )

        frames.append(df)

    return pd.concat(frames, ignore_index=True)


def validate_join() -> None:
    """Measure salary-to-player-stat join coverage."""
    stats = load_player_stats()
    salaries = load_salaries()

    # Only evaluate salary rows that contain an NBA player ID.
    mapped_salaries = salaries[
        salaries["player_id"].notna()
    ].copy()

    mapped_salaries["player_id"] = (
        mapped_salaries["player_id"].astype(int)
    )

    stats["PLAYER_ID"] = stats["PLAYER_ID"].astype(int)

    joined = mapped_salaries.merge(
        stats,
        how="left",
        left_on=["player_id", "SEASON"],
        right_on=["PLAYER_ID", "SEASON"],
        indicator=True,
    )

    matched = (joined["_merge"] == "both").sum()
    unmatched = (joined["_merge"] == "left_only").sum()
    total = len(joined)

    coverage = matched / total * 100 if total else 0

    print("\nSalary → Player Stats Join")
    print("--------------------------")
    print(f"Mapped salary rows: {total:,}")
    print(f"Matched rows: {matched:,}")
    print(f"Unmatched rows: {unmatched:,}")
    print(f"Join coverage: {coverage:.2f}%")

    if unmatched:
        unmatched_df = joined[
            joined["_merge"] == "left_only"
        ][
            [
                "SEASON",
                "player_id",
                "bbref_id",
                "team_id",
                "salary",
            ]
        ]

        print("\nSample unmatched salary records:")
        print(unmatched_df.head(20).to_string(index=False))


if __name__ == "__main__":
    validate_join()