from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
CAP_FILE = Path("data/reference/salary_cap.csv")


def salary_year_to_season(year: int) -> str:
    """Convert salary year 2026 to NBA season 2025-26."""
    start_year = year - 1
    return f"{start_year}-{str(year)[-2:]}"


def load_salaries() -> pd.DataFrame:
    """Load and combine all raw salary files."""
    files = sorted(RAW_DATA_DIR.glob("salaries_*.csv"))

    frames = []

    for file in files:
        df = pd.read_csv(file)

        df["SEASON"] = df["season"].apply(
            lambda year: salary_year_to_season(int(year))
        )

        frames.append(df)

    return pd.concat(frames, ignore_index=True)


def build_salary_metrics() -> pd.DataFrame:
    """Build analytics-ready NBA salary metrics."""
    salaries = load_salaries()
    caps = pd.read_csv(CAP_FILE)

    caps = caps.rename(columns={"season": "SEASON"})

    df = salaries.merge(
        caps,
        on="SEASON",
        how="left",
        validate="many_to_one",
    )

    df["salary_cap_pct"] = (
        df["salary"] / df["salary_cap"] * 100
    ).round(2)

    df["luxury_tax_pct"] = (
        df["salary"] / df["luxury_tax"] * 100
    ).round(2)

    return df


def save_salary_metrics(df: pd.DataFrame) -> Path:
    """Save processed salary metrics."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_DATA_DIR / "salary_metrics.csv"

    df.to_csv(output_path, index=False)

    return output_path


def main() -> None:
    df = build_salary_metrics()

    print("\nSalary Metrics")
    print("--------------")
    print(f"Rows: {len(df):,}")
    print(f"Seasons: {df['SEASON'].nunique()}")
    print(f"Missing salary caps: {df['salary_cap'].isna().sum()}")

    print("\nSample:")
    print(
        df[
            [
                "SEASON",
                "player_id",
                "team_id",
                "salary",
                "salary_cap",
                "salary_cap_pct",
            ]
        ].head(10).to_string(index=False)
    )

    print("\nHighest salary as % of cap:")
    print(
        df[
            [
                "SEASON",
                "player_id",
                "salary",
                "salary_cap_pct",
            ]
        ]
        .sort_values("salary_cap_pct", ascending=False)
        .head(10)
        .to_string(index=False)
    )

    output_path = save_salary_metrics(df)

    print(f"\nSaved processed data to {output_path}")


if __name__ == "__main__":
    main()