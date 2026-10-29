from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw")
EXPECTED_SEASONS = 26

REQUIRED_COLUMNS = {
    "SEASON",
    "TEAM_ID",
    "TEAM_NAME",
    "GP",
    "W",
    "L",
    "W_PCT",
    "PTS",
}


def validate_team_stats() -> bool:
    """Validate all extracted NBA team-season files."""
    files = sorted(RAW_DATA_DIR.glob("team_stats_*.csv"))

    print(f"Found {len(files)} team stats files.\n")

    issues = []
    total_rows = 0
    reference_columns = None

    for file in files:
        df = pd.read_csv(file)
        total_rows += len(df)

        season = df["SEASON"].iloc[0] if not df.empty else "UNKNOWN"

        # Required columns
        missing_columns = REQUIRED_COLUMNS - set(df.columns)

        if missing_columns:
            issues.append(
                f"{season}: missing columns {sorted(missing_columns)}"
            )

        # Team IDs should never be null
        if df["TEAM_ID"].isna().any():
            issues.append(f"{season}: null TEAM_ID values")

        # One row per team per season
        duplicate_teams = df["TEAM_ID"].duplicated().sum()

        if duplicate_teams:
            issues.append(
                f"{season}: {duplicate_teams} duplicate TEAM_ID values"
            )

        # Exactly one season value per file
        if df["SEASON"].nunique() != 1:
            issues.append(f"{season}: multiple SEASON values found")

        # Basic sanity checks
        if (df["GP"] < 0).any():
            issues.append(f"{season}: negative games played")

        if (df["W"] < 0).any():
            issues.append(f"{season}: negative wins")

        if (df["L"] < 0).any():
            issues.append(f"{season}: negative losses")

        if (df["PTS"] < 0).any():
            issues.append(f"{season}: negative points")

        if ((df["W_PCT"] < 0) | (df["W_PCT"] > 1)).any():
            issues.append(f"{season}: invalid win percentage")

        # Normally W + L should equal GP
        invalid_records = df[(df["W"] + df["L"]) != df["GP"]]

        if not invalid_records.empty:
            issues.append(
                f"{season}: {len(invalid_records)} teams where W + L != GP"
            )

        # Schema consistency
        current_columns = set(df.columns)

        if reference_columns is None:
            reference_columns = current_columns
        elif current_columns != reference_columns:
            missing = reference_columns - current_columns
            added = current_columns - reference_columns

            issues.append(
                f"{season}: schema differs "
                f"(missing={sorted(missing)}, added={sorted(added)})"
            )

        print(
            f"[CHECK] {season}: "
            f"{len(df)} teams | "
            f"{len(df.columns)} columns | "
            f"{duplicate_teams} duplicate teams"
        )

    if len(files) != EXPECTED_SEASONS:
        issues.append(
            f"Expected {EXPECTED_SEASONS} season files, found {len(files)}"
        )

    print("\nValidation summary")
    print("------------------")
    print(f"Season files: {len(files)}")
    print(f"Total team-season rows: {total_rows:,}")
    print(f"Issues found: {len(issues)}")

    if issues:
        print("\nIssues:")

        for issue in issues:
            print(f"- {issue}")

        return False

    print("\nAll validation checks passed.")
    return True


if __name__ == "__main__":
    success = validate_team_stats()

    if not success:
        raise SystemExit(1)