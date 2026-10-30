from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


PROCESSED_DATA_DIR = Path("data/processed")
DATABASE_URL = "postgresql+psycopg://localhost/nba_analytics"

TRADES_FILE = PROCESSED_DATA_DIR / "trades_normalized.csv"
TRADE_TEAMS_FILE = PROCESSED_DATA_DIR / "trade_teams_mapped.csv"
TRADE_ASSETS_FILE = PROCESSED_DATA_DIR / "trade_assets_resolved.csv"


def get_engine():
    """Create PostgreSQL connection."""
    return create_engine(DATABASE_URL)


def load_season_lookup(engine) -> dict:
    """Map season strings to warehouse season IDs."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT season_id, season
                FROM seasons
                """
            )
        )

        return {
            row.season: row.season_id
            for row in rows
        }


def trade_date_to_season(trade_date) -> str:
    """Convert a trade date to its NBA season.

    July-December belongs to the season beginning that year.
    January-June belongs to the season beginning the prior year.
    """
    date = pd.Timestamp(trade_date)

    if date.month >= 7:
        start_year = date.year
    else:
        start_year = date.year - 1

    end_year = start_year + 1

    return (
        f"{start_year}-"
        f"{str(end_year)[-2:]}"
    )


def prepare_trades(engine) -> pd.DataFrame:
    """Prepare trade records for PostgreSQL."""
    df = pd.read_csv(TRADES_FILE)

    df["date"] = pd.to_datetime(
        df["date"],
        errors="raise",
    )

    df["season"] = df["date"].apply(
        trade_date_to_season
    )

    season_lookup = load_season_lookup(
        engine
    )

    df["season_id"] = df["season"].map(
        season_lookup
    )

    if df["season_id"].isna().any():
        missing = (
            df.loc[
                df["season_id"].isna(),
                "season",
            ]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            f"Missing season IDs: {missing}"
        )

    prepared = df[
        [
            "trade_id",
            "date",
            "season_id",
            "player_or_assets",
            "notes",
        ]
    ].copy()

    prepared = prepared.rename(
        columns={
            "date": "trade_date",
            "player_or_assets": "description",
        }
    )

    prepared["season_id"] = (
        prepared["season_id"]
        .astype("int64")
    )

    return prepared


def prepare_trade_teams() -> pd.DataFrame:
    """Prepare trade/team bridge records."""
    df = pd.read_csv(
        TRADE_TEAMS_FILE
    )

    prepared = df[
        [
            "trade_id",
            "team_id",
        ]
    ].copy()

    prepared["trade_id"] = (
        prepared["trade_id"]
        .astype("int64")
    )

    prepared["team_id"] = (
        prepared["team_id"]
        .astype("int64")
    )

    return prepared.drop_duplicates()


def prepare_trade_assets() -> pd.DataFrame:
    """Prepare normalized trade assets."""
    df = pd.read_csv(
        TRADE_ASSETS_FILE
    )

    prepared = df[
        [
            "trade_id",
            "team_id",
            "asset_type",
            "asset_description",
            "player_id",
            "match_method",
        ]
    ].copy()

    prepared = prepared.rename(
        columns={
            "team_id": "receiving_team_id",
            "match_method": "player_match_method",
        }
    )

    prepared["trade_id"] = (
        prepared["trade_id"]
        .astype("int64")
    )

    prepared["receiving_team_id"] = (
        prepared["receiving_team_id"]
        .astype("int64")
    )

    prepared["player_id"] = (
        prepared["player_id"]
        .astype("Int64")
    )

    return prepared


def load_data(
    engine,
    trades: pd.DataFrame,
    trade_teams: pd.DataFrame,
    trade_assets: pd.DataFrame,
) -> None:
    """Load normalized trade data in FK-safe order."""

    trades.to_sql(
        "trades",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )

    print(
        f"[LOADED] trades: "
        f"{len(trades):,} rows"
    )

    trade_teams.to_sql(
        "trade_teams",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print(
        f"[LOADED] trade_teams: "
        f"{len(trade_teams):,} rows"
    )

    trade_assets.to_sql(
        "trade_assets",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print(
        f"[LOADED] trade_assets: "
        f"{len(trade_assets):,} rows"
    )


def verify_load(engine) -> None:
    """Verify trade warehouse tables."""
    queries = {
        "Trades": """
            SELECT COUNT(*)
            FROM trades
        """,
        "Trade/team relationships": """
            SELECT COUNT(*)
            FROM trade_teams
        """,
        "Trade assets": """
            SELECT COUNT(*)
            FROM trade_assets
        """,
        "Player assets": """
            SELECT COUNT(*)
            FROM trade_assets
            WHERE asset_type = 'PLAYER_CANDIDATE'
        """,
        "Resolved player assets": """
            SELECT COUNT(*)
            FROM trade_assets
            WHERE asset_type = 'PLAYER_CANDIDATE'
              AND player_id IS NOT NULL
        """,
        "Unresolved player assets": """
            SELECT COUNT(*)
            FROM trade_assets
            WHERE asset_type = 'PLAYER_CANDIDATE'
              AND player_id IS NULL
        """,
        "Multi-team trades": """
            SELECT COUNT(*)
            FROM (
                SELECT trade_id
                FROM trade_teams
                GROUP BY trade_id
                HAVING COUNT(*) >= 3
            ) x
        """,
    }

    print("\nDatabase verification")
    print("---------------------")

    with engine.connect() as connection:
        for label, query in queries.items():
            value = connection.execute(
                text(query)
            ).scalar()

            print(
                f"{label}: {value:,}"
            )


def main() -> None:
    engine = get_engine()

    trades = prepare_trades(engine)
    trade_teams = prepare_trade_teams()
    trade_assets = prepare_trade_assets()

    print("Prepared trade warehouse data")
    print("-----------------------------")
    print(
        f"Trades: {len(trades):,}"
    )
    print(
        f"Trade/team relationships: "
        f"{len(trade_teams):,}"
    )
    print(
        f"Trade assets: "
        f"{len(trade_assets):,}"
    )

    load_data(
        engine,
        trades,
        trade_teams,
        trade_assets,
    )

    verify_load(engine)

    engine.dispose()


if __name__ == "__main__":
    main()