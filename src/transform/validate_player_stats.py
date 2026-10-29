from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw")
EXPECTED_SEASONS = 26


def validate_player_stats() -> bool:
    """Validate all extracted NBA player season files."""
    files = sorted(RAW_DATA_DIR.glob("player_stats_*.csv"))

    print(f"Found {len(files)} player stats files.\n")

    issues = []
    total_rows = 0
    reference_columns = None

    for file in files:
        df = pd.read_csv(file)
        total_rows += len(df)

        season = df["SEASON"].iloc[0] if not df.empty else "UNKNOWN"

        # Check required columns
        required_columns = {
            "SEASON",
            "PLAYER_ID",
            "PLAYER_NAME",
            "TEAM_ID",
            "GP",
            "MIN",
            "PTS",
            "REB",
            "AST",
        }

        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            issues.append(
                f"{season}: missing columns {sorted(missing_columns)}"
            )

        # Check null primary identifiers
        if df["PLAYER_ID"].isna().any():
            issues.append(f"{season}: null PLAYER_ID values")

        # One season-level row per player
        duplicate_players = df["PLAYER_ID"].duplicated().sum()

        if duplicate_players:
            issues.append(
                f"{season}: {duplicate_players} duplicate PLAYER_ID values"
            )

        # Validate season column
        if df["SEASON"].nunique() != 1:
            issues.append(f"{season}: multiple SEASON values found")

        # Basic numeric sanity checks
        if (df["GP"] < 0).any():
            issues.append(f"{season}: negative games played")

        if (df["MIN"] < 0).any():
            issues.append(f"{season}: negative minutes")

        if (df["PTS"] < 0).any():
            issues.append(f"{season}: negative points")

        # Compare schemas between seasons
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
            f"{len(df):,} rows | "
            f"{len(df.columns)} columns | "
            f"{duplicate_players} duplicate players"
        )

    if len(files) != EXPECTED_SEASONS:
        issues.append(
            f"Expected {EXPECTED_SEASONS} season files, found {len(files)}"
        )

    print("\nValidation summary")
    print("------------------")
    print(f"Season files: {len(files)}")
    print(f"Total player-season rows: {total_rows:,}")
    print(f"Issues found: {len(issues)}")

    if issues:
        print("\nIssues:")

        for issue in issues:
            print(f"- {issue}")

        return False

    print("\nAll validation checks passed.")
    return True


if __name__ == "__main__":
    success = validate_player_stats()

    if not success:
        raise SystemExit(1)