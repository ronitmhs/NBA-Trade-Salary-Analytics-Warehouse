from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw")
EXPECTED_FILES = 17


def salary_year_to_season(year: int) -> str:
    """Convert 2026 to 2025-26."""
    start_year = year - 1
    return f"{start_year}-{str(year)[-2:]}"


def validate_salaries() -> bool:
    """Validate salary files and measure NBA ID coverage."""
    files = sorted(RAW_DATA_DIR.glob("salaries_*.csv"))

    print(f"Found {len(files)} salary files.\n")

    issues = []
    total_rows = 0
    mapped_player_ids = 0
    null_player_ids = 0
    duplicate_rows = 0

    for file in files:
        df = pd.read_csv(file)

        total_rows += len(df)

        salary_year = int(df["season"].iloc[0])
        nba_season = salary_year_to_season(salary_year)

        mapped = df["player_id"].notna().sum()
        null_ids = df["player_id"].isna().sum()

        duplicates = df.duplicated(
            subset=["season", "team_id", "bbref_id"]
        ).sum()

        mapped_player_ids += mapped
        null_player_ids += null_ids
        duplicate_rows += duplicates

        if (df["salary"] < 0).any():
            issues.append(f"{nba_season}: negative salary found")

        if df["team_id"].isna().any():
            issues.append(f"{nba_season}: null team_id found")

        if duplicates:
            issues.append(
                f"{nba_season}: {duplicates} duplicate salary rows"
            )

        coverage = (mapped / len(df)) * 100 if len(df) else 0

        print(
            f"[CHECK] {nba_season}: "
            f"{len(df):,} rows | "
            f"{mapped:,} mapped IDs | "
            f"{null_ids:,} null IDs | "
            f"{coverage:.1f}% ID coverage"
        )

    if len(files) != EXPECTED_FILES:
        issues.append(
            f"Expected {EXPECTED_FILES} salary files, found {len(files)}"
        )

    overall_coverage = (
        mapped_player_ids / total_rows * 100
        if total_rows
        else 0
    )

    print("\nValidation summary")
    print("------------------")
    print(f"Salary files: {len(files)}")
    print(f"Total salary rows: {total_rows:,}")
    print(f"Mapped NBA player IDs: {mapped_player_ids:,}")
    print(f"Null NBA player IDs: {null_player_ids:,}")
    print(f"NBA ID coverage: {overall_coverage:.2f}%")
    print(f"Duplicate rows: {duplicate_rows}")
    print(f"Issues found: {len(issues)}")

    if issues:
        print("\nIssues:")

        for issue in issues:
            print(f"- {issue}")

        return False

    print("\nAll structural validation checks passed.")
    return True


if __name__ == "__main__":
    success = validate_salaries()

    if not success:
        raise SystemExit(1)