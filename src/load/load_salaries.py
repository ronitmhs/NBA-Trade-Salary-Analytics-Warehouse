from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


PROCESSED_DATA_DIR = Path("data/processed")
DATABASE_URL = "postgresql+psycopg://localhost/nba_analytics"


def get_engine():
    """Create PostgreSQL connection."""
    return create_engine(DATABASE_URL)


def load_season_lookup(engine) -> dict:
    """Map NBA season strings to database season IDs."""
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT season_id, season FROM seasons")
        )

        return {
            row.season: row.season_id
            for row in rows
        }


def load_valid_player_ids(engine) -> set:
    """Load valid NBA player IDs from the player dimension."""
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT player_id FROM players")
        )

        return {
            row.player_id
            for row in rows
        }


def prepare_salaries(engine) -> pd.DataFrame:
    """Prepare processed salary metrics for PostgreSQL."""
    file = PROCESSED_DATA_DIR / "salary_metrics.csv"

    df = pd.read_csv(file)

    # Keep unknown-salary records in the source data, but do not
    # load them as financial facts into the warehouse.
    missing_salary_count = df["salary"].isna().sum()

    if missing_salary_count:
        print(
            f"[INFO] Excluding {missing_salary_count:,} rows "
            "with unknown salary values."
        )

    df = df[df["salary"].notna()].copy()

    # Validate source player IDs against our player dimension.
    valid_player_ids = load_valid_player_ids(engine)

    invalid_player_mask = (
        df["player_id"].notna()
        & ~df["player_id"].isin(valid_player_ids)
    )

    invalid_player_count = invalid_player_mask.sum()

    invalid_unique_players = df.loc[
        invalid_player_mask,
        "player_id",
    ].nunique()

    if invalid_player_count:
        print(
            f"[INFO] Setting player_id to NULL for "
            f"{invalid_player_count:,} salary rows "
            f"covering {invalid_unique_players:,} player IDs "
            "not found in the players dimension."
        )

        df.loc[
            invalid_player_mask,
            "player_id",
        ] = pd.NA

    # Map season strings such as 2025-26 to warehouse season IDs.
    season_lookup = load_season_lookup(engine)

    df["season_id"] = df["SEASON"].map(
        season_lookup
    )

    if df["season_id"].isna().any():
        missing = df.loc[
            df["season_id"].isna(),
            "SEASON",
        ].unique()

        raise ValueError(
            f"Missing season IDs for: {missing}"
        )

    # Select only columns used by the warehouse fact table.
    columns = [
        "player_id",
        "team_id",
        "season_id",
        "bbref_id",
        "salary",
        "salary_cap",
        "luxury_tax",
        "salary_cap_pct",
        "luxury_tax_pct",
    ]

    df = df[columns].copy()

    # player_id is nullable because some salary records cannot
    # currently be resolved to our NBA player dimension.
    df["player_id"] = df["player_id"].astype("Int64")

    df["team_id"] = df["team_id"].astype("int64")
    df["season_id"] = df["season_id"].astype("int64")

    df["salary"] = df["salary"].astype("int64")
    df["salary_cap"] = df["salary_cap"].astype("int64")
    df["luxury_tax"] = df["luxury_tax"].astype("int64")

    return df


def load_salaries(
    engine,
    df: pd.DataFrame,
) -> None:
    """Load known salary facts into PostgreSQL."""
    df.to_sql(
        "player_salaries",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print(
        f"[LOADED] player_salaries: "
        f"{len(df):,} rows"
    )


def verify_load(engine) -> None:
    """Verify salary data after loading."""
    queries = {
        "Total rows": """
            SELECT COUNT(*)
            FROM player_salaries
        """,
        "Mapped players": """
            SELECT COUNT(*)
            FROM player_salaries
            WHERE player_id IS NOT NULL
        """,
        "Unmapped players": """
            SELECT COUNT(*)
            FROM player_salaries
            WHERE player_id IS NULL
        """,
        "Seasons": """
            SELECT COUNT(DISTINCT season_id)
            FROM player_salaries
        """,
        "Teams": """
            SELECT COUNT(DISTINCT team_id)
            FROM player_salaries
        """,
    }

    print("\nDatabase verification")
    print("---------------------")

    with engine.connect() as connection:
        for label, query in queries.items():
            value = connection.execute(
                text(query)
            ).scalar()

            print(f"{label}: {value:,}")


def main() -> None:
    engine = get_engine()

    df = prepare_salaries(engine)

    print(
        f"Prepared {len(df):,} salary rows."
    )

    load_salaries(engine, df)

    verify_load(engine)

    engine.dispose()


if __name__ == "__main__":
    main()