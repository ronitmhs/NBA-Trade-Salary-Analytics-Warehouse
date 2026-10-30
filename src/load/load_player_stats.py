from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


RAW_DATA_DIR = Path("data/raw")
DATABASE_URL = "postgresql+psycopg://localhost/nba_analytics"


COLUMN_MAP = {
    "PLAYER_ID": "player_id",
    "AGE": "age",
    "GP": "games_played",
    "W": "wins",
    "L": "losses",
    "W_PCT": "win_pct",
    "MIN": "minutes",
    "FGM": "field_goals_made",
    "FGA": "field_goals_attempted",
    "FG_PCT": "field_goal_pct",
    "FG3M": "three_pointers_made",
    "FG3A": "three_pointers_attempted",
    "FG3_PCT": "three_point_pct",
    "FTM": "free_throws_made",
    "FTA": "free_throws_attempted",
    "FT_PCT": "free_throw_pct",
    "OREB": "offensive_rebounds",
    "DREB": "defensive_rebounds",
    "REB": "rebounds",
    "AST": "assists",
    "TOV": "turnovers",
    "STL": "steals",
    "BLK": "blocks",
    "PTS": "points",
    "PLUS_MINUS": "plus_minus",
    "TEAM_COUNT": "team_count",
}


def get_engine():
    """Create PostgreSQL connection."""
    return create_engine(DATABASE_URL)


def load_season_lookup(engine) -> dict:
    """Map season strings to PostgreSQL season IDs."""
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT season_id, season FROM seasons")
        )

        return {
            row.season: row.season_id
            for row in rows
        }


def prepare_player_stats(engine) -> pd.DataFrame:
    """Transform raw NBA season files for PostgreSQL."""
    files = sorted(RAW_DATA_DIR.glob("player_stats_*.csv"))

    frames = []

    for file in files:
        df = pd.read_csv(file)

        selected = df[
            ["SEASON"] + list(COLUMN_MAP.keys())
        ].copy()

        selected = selected.rename(columns=COLUMN_MAP)

        frames.append(selected)

    combined = pd.concat(frames, ignore_index=True)

    season_lookup = load_season_lookup(engine)

    combined["season_id"] = combined["SEASON"].map(
        season_lookup
    )

    if combined["season_id"].isna().any():
        missing = combined.loc[
            combined["season_id"].isna(),
            "SEASON"
        ].unique()

        raise ValueError(
            f"Missing season IDs for: {missing}"
        )

    combined = combined.drop(columns=["SEASON"])

    combined["season_id"] = combined["season_id"].astype(int)

    return combined


def load_player_stats(engine, df: pd.DataFrame) -> None:
    """Load player-season facts into PostgreSQL."""
    df.to_sql(
        "player_season_stats",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print(
        f"[LOADED] player_season_stats: "
        f"{len(df):,} rows"
    )


def verify_load(engine) -> None:
    """Verify player stats after loading."""
    queries = {
        "Total rows": """
            SELECT COUNT(*)
            FROM player_season_stats
        """,
        "Unique players": """
            SELECT COUNT(DISTINCT player_id)
            FROM player_season_stats
        """,
        "Seasons": """
            SELECT COUNT(DISTINCT season_id)
            FROM player_season_stats
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

    df = prepare_player_stats(engine)

    print(f"Prepared {len(df):,} player-season rows.")

    load_player_stats(engine, df)
    verify_load(engine)

    engine.dispose()


if __name__ == "__main__":
    main()