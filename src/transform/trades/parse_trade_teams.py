from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

TRADE_FILE = RAW_DATA_DIR / "trades.csv"


def load_trades() -> pd.DataFrame:
    """Load raw trade records."""
    df = pd.read_csv(TRADE_FILE)

    df = df[
        df["kind"].str.lower().eq("trade")
    ].copy()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    return df.reset_index(drop=True)


def create_trade_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Assign stable internal trade IDs."""
    df = df.copy()

    df["trade_id"] = (
        df.index + 1
    )

    return df


def parse_trade_teams(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Convert trade team strings into one row per trade/team."""

    records = []

    for row in df.itertuples():
        teams = [
            team.strip()
            for team in row.teams.split("/")
            if team.strip()
        ]

        for team in teams:
            records.append(
                {
                    "trade_id": row.trade_id,
                    "trade_date": row.date,
                    "team_abbreviation": team,
                }
            )

    return pd.DataFrame(records)


def validate_trade_teams(
    trades: pd.DataFrame,
    trade_teams: pd.DataFrame,
) -> None:
    """Validate normalized trade-team relationships."""

    issues = []

    duplicates = trade_teams.duplicated(
        subset=[
            "trade_id",
            "team_abbreviation",
        ]
    ).sum()

    if duplicates:
        issues.append(
            f"{duplicates} duplicate trade/team relationships"
        )

    trade_counts = (
        trade_teams.groupby("trade_id")
        ["team_abbreviation"]
        .nunique()
    )

    missing_trades = set(
        trades["trade_id"]
    ) - set(
        trade_teams["trade_id"]
    )

    if missing_trades:
        issues.append(
            f"{len(missing_trades)} trades have no teams"
        )

    print("\nTrade team normalization")
    print("------------------------")
    print(f"Trades: {len(trades):,}")
    print(
        f"Trade/team relationships: "
        f"{len(trade_teams):,}"
    )
    print(
        f"Unique team abbreviations: "
        f"{trade_teams['team_abbreviation'].nunique()}"
    )
    print(f"Duplicate relationships: {duplicates}")

    print("\nTeams per trade:")
    print(
        trade_counts
        .value_counts()
        .sort_index()
        .to_string()
    )

    print(f"\nIssues found: {len(issues)}")

    if issues:
        for issue in issues:
            print(f"- {issue}")
    else:
        print(
            "All trade/team structural checks passed."
        )


def save_outputs(
    trades: pd.DataFrame,
    trade_teams: pd.DataFrame,
) -> None:
    """Save normalized trade data locally."""
    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    trades_output = (
        PROCESSED_DATA_DIR
        / "trades_normalized.csv"
    )

    teams_output = (
        PROCESSED_DATA_DIR
        / "trade_teams.csv"
    )

    trades[
        [
            "trade_id",
            "date",
            "teams",
            "player_or_assets",
            "notes",
        ]
    ].to_csv(
        trades_output,
        index=False,
    )

    trade_teams.to_csv(
        teams_output,
        index=False,
    )

    print(
        f"\nSaved {trades_output}"
    )

    print(
        f"Saved {teams_output}"
    )


def main() -> None:
    trades = load_trades()

    trades = create_trade_ids(trades)

    trade_teams = parse_trade_teams(trades)

    validate_trade_teams(
        trades,
        trade_teams,
    )

    save_outputs(
        trades,
        trade_teams,
    )


if __name__ == "__main__":
    main()