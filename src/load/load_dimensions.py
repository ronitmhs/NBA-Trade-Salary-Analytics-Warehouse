from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


RAW_DATA_DIR = Path("data/raw")

DATABASE_URL = "postgresql+psycopg://localhost/nba_analytics"


def get_engine():
    """Create a PostgreSQL database connection."""
    return create_engine(DATABASE_URL)


def load_players(engine) -> None:
    """Load NBA player reference data."""
    df = pd.read_csv(RAW_DATA_DIR / "players.csv")

    df = df.rename(
        columns={
            "id": "player_id",
        }
    )

    df.to_sql(
        "players",
        engine,
        if_exists="append",
        index=False,
        method="multi",
    )

    print(f"[LOADED] players: {len(df):,} rows")


def load_teams(engine) -> None:
    """Load NBA team reference data."""
    df = pd.read_csv(RAW_DATA_DIR / "teams.csv")

    df = df.rename(
        columns={
            "id": "team_id",
        }
    )

    df.to_sql(
        "teams",
        engine,
        if_exists="append",
        index=False,
        method="multi",
    )

    print(f"[LOADED] teams: {len(df):,} rows")


def load_seasons(engine) -> None:
    """Generate and load NBA seasons."""
    seasons = []

    for start_year in range(2000, 2026):
        end_year = start_year + 1

        season = f"{start_year}-{str(end_year)[-2:]}"

        seasons.append(
            {
                "season": season,
                "start_year": start_year,
                "end_year": end_year,
            }
        )

    df = pd.DataFrame(seasons)

    df.to_sql(
        "seasons",
        engine,
        if_exists="append",
        index=False,
        method="multi",
    )

    print(f"[LOADED] seasons: {len(df):,} rows")


def verify_load(engine) -> None:
    """Verify row counts after loading."""
    tables = ["players", "teams", "seasons"]

    print("\nDatabase row counts")
    print("-------------------")

    with engine.connect() as connection:
        for table in tables:
            result = connection.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            )

            count = result.scalar()

            print(f"{table}: {count:,}")


def main() -> None:
    engine = get_engine()

    load_players(engine)
    load_teams(engine)
    load_seasons(engine)

    verify_load(engine)

    engine.dispose()


if __name__ == "__main__":
    main()