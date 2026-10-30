from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw")
TRADE_FILE = RAW_DATA_DIR / "trades.csv"


def load_trades() -> pd.DataFrame:
    """Load raw NBA trade transaction data."""
    df = pd.read_csv(TRADE_FILE)

    # Keep only trade records.
    df = df[
        df["kind"].str.lower().eq("trade")
    ].copy()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    return df


def validate_trades(df: pd.DataFrame) -> None:
    """Run basic structural checks on trade data."""
    required_columns = {
        "date",
        "kind",
        "teams",
        "player_or_assets",
        "notes",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    print("\nTrade dataset")
    print("-------------")
    print(f"Rows: {len(df):,}")
    print(
        f"Date range: "
        f"{df['date'].min().date()} to "
        f"{df['date'].max().date()}"
    )
    print(
        f"Missing dates: "
        f"{df['date'].isna().sum()}"
    )
    print(
        f"Missing teams: "
        f"{df['teams'].isna().sum()}"
    )
    print(
        f"Missing notes: "
        f"{df['notes'].isna().sum()}"
    )


def inspect_team_counts(df: pd.DataFrame) -> None:
    """Inspect two-team and multi-team trade counts."""
    team_counts = (
        df["teams"]
        .str.split("/")
        .apply(
            lambda teams: len(teams)
            if isinstance(teams, list)
            else 0
        )
    )

    print("\nTeams per trade")
    print("---------------")
    print(
        team_counts
        .value_counts()
        .sort_index()
        .to_string()
    )

    multi_team = df[team_counts >= 3]

    print(
        f"\nMulti-team trades: "
        f"{len(multi_team):,}"
    )

    if not multi_team.empty:
        print("\nSample multi-team trades:")

        print(
            multi_team[
                [
                    "date",
                    "teams",
                    "player_or_assets",
                ]
            ]
            .head(5)
            .to_string(index=False)
        )


def main() -> None:
    trades = load_trades()

    validate_trades(trades)
    inspect_team_counts(trades)


if __name__ == "__main__":
    main()