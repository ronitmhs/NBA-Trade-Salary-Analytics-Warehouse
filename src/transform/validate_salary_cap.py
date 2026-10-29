from pathlib import Path

import pandas as pd


CAP_FILE = Path("data/reference/salary_cap.csv")
EXPECTED_SEASONS = 17


def validate_salary_cap() -> bool:
    """Validate NBA salary cap reference data."""
    df = pd.read_csv(CAP_FILE)

    issues = []

    required_columns = {
        "season",
        "salary_cap",
        "luxury_tax",
    }

    missing = required_columns - set(df.columns)

    if missing:
        issues.append(f"Missing columns: {sorted(missing)}")

    if len(df) != EXPECTED_SEASONS:
        issues.append(
            f"Expected {EXPECTED_SEASONS} seasons, found {len(df)}"
        )

    if df["season"].duplicated().any():
        issues.append("Duplicate seasons found")

    if df["salary_cap"].isna().any():
        issues.append("Null salary cap values found")

    if (df["salary_cap"] <= 0).any():
        issues.append("Invalid salary cap values found")

    if (df["luxury_tax"] <= df["salary_cap"]).any():
        issues.append(
            "Luxury tax must be greater than salary cap"
        )

    print("Salary Cap Validation")
    print("---------------------")
    print(f"Seasons: {len(df)}")
    print(f"First season: {df['season'].iloc[0]}")
    print(f"Last season: {df['season'].iloc[-1]}")
    print(
        f"Cap range: "
        f"${df['salary_cap'].min():,.0f} - "
        f"${df['salary_cap'].max():,.0f}"
    )
    print(f"Issues found: {len(issues)}")

    if issues:
        print("\nIssues:")

        for issue in issues:
            print(f"- {issue}")

        return False

    print("\nAll salary cap validation checks passed.")
    return True


if __name__ == "__main__":
    success = validate_salary_cap()

    if not success:
        raise SystemExit(1)