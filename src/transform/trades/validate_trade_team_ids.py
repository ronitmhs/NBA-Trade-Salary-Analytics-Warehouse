from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


PROCESSED_DATA_DIR = Path("data/processed")
DATABASE_URL = "postgresql+psycopg://localhost/nba_analytics"


def load_trade_teams() -> pd.DataFrame:
    """Load normalized trade-team relationships."""
    return pd.read_csv(
        PROCESSED_DATA_DIR / "trade_teams.csv"
    )


def load_team_dimension(engine) -> pd.DataFrame:
    """Load NBA team IDs and abbreviations from PostgreSQL."""
    query = """
        SELECT
            team_id,
            abbreviation
        FROM teams
    """

    return pd.read_sql(
        text(query),
        engine,
    )


def map_team_ids(
    trade_teams: pd.DataFrame,
    teams: pd.DataFrame,
) -> pd.DataFrame:
    """Map trade abbreviations to NBA team IDs."""
    df = trade_teams.merge(
        teams,
        how="left",
        left_on="team_abbreviation",
        right_on="abbreviation",
        validate="many_to_one",
    )

    return df


def validate_mapping(df: pd.DataFrame) -> None:
    """Validate trade-team ID mapping."""
    missing = df[df["team_id"].isna()]

    print("\nTrade Team ID Mapping")
    print("---------------------")
    print(f"Relationships: {len(df):,}")
    print(
        f"Mapped team IDs: "
        f"{df['team_id'].notna().sum():,}"
    )
    print(
        f"Unmapped team IDs: "
        f"{df['team_id'].isna().sum():,}"
    )
    print(
        f"Unique NBA teams: "
        f"{df['team_id'].nunique()}"
    )

    if not missing.empty:
        print("\nUnmapped abbreviations:")

        print(
            missing[
                "team_abbreviation"
            ]
            .drop_duplicates()
            .sort_values()
            .to_string(index=False)
        )
    else:
        print(
            "\nAll trade team abbreviations "
            "mapped successfully."
        )


def save_mapped_trade_teams(
    df: pd.DataFrame,
) -> None:
    """Save mapped trade-team relationships."""
    output = (
        PROCESSED_DATA_DIR
        / "trade_teams_mapped.csv"
    )

    df[
        [
            "trade_id",
            "trade_date",
            "team_id",
            "team_abbreviation",
        ]
    ].to_csv(
        output,
        index=False,
    )

    print(f"\nSaved {output}")


def main() -> None:
    engine = create_engine(DATABASE_URL)

    trade_teams = load_trade_teams()
    teams = load_team_dimension(engine)

    mapped = map_team_ids(
        trade_teams,
        teams,
    )

    validate_mapping(mapped)

    if mapped["team_id"].isna().any():
        raise SystemExit(
            "Trade team mapping failed."
        )

    mapped["team_id"] = (
        mapped["team_id"].astype("int64")
    )

    save_mapped_trade_teams(mapped)

    engine.dispose()


if __name__ == "__main__":
    main()