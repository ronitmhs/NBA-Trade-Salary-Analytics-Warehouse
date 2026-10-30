from pathlib import Path
import re
import unicodedata

import pandas as pd
from sqlalchemy import create_engine, text


PROCESSED_DATA_DIR = Path("data/processed")
REFERENCE_DATA_DIR = Path("data/reference")

DATABASE_URL = "postgresql+psycopg://localhost/nba_analytics"

ASSET_FILE = (
    PROCESSED_DATA_DIR / "trade_assets_parsed.csv"
)

ALIAS_FILE = (
    REFERENCE_DATA_DIR / "player_aliases.csv"
)


def normalize_name(name: str) -> str:
    """Normalize a player name for deterministic matching."""
    if pd.isna(name):
        return ""

    name = unicodedata.normalize(
        "NFKD",
        str(name),
    )

    name = "".join(
        char
        for char in name
        if not unicodedata.combining(char)
    )

    name = name.lower()
    name = name.replace("’", "'")

    name = re.sub(
        r"[^a-z0-9 ]",
        "",
        name,
    )

    name = re.sub(
        r"\s+",
        " ",
        name,
    ).strip()

    return name


def load_assets() -> pd.DataFrame:
    """Load parsed trade assets."""
    return pd.read_csv(ASSET_FILE)


def load_players(engine) -> pd.DataFrame:
    """Load player dimension from PostgreSQL."""
    query = """
        SELECT
            player_id,
            full_name
        FROM players
    """

    return pd.read_sql(
        text(query),
        engine,
    )


def load_aliases() -> pd.DataFrame:
    """Load reviewed player-name aliases."""
    if not ALIAS_FILE.exists():
        return pd.DataFrame(
            columns=[
                "source_name",
                "canonical_name",
            ]
        )

    return pd.read_csv(ALIAS_FILE)


def build_player_lookup(
    players: pd.DataFrame,
) -> dict:
    """Build lookup containing only unique normalized names."""
    players = players.copy()

    players["normalized_name"] = (
        players["full_name"]
        .apply(normalize_name)
    )

    counts = (
        players.groupby("normalized_name")
        ["player_id"]
        .nunique()
    )

    unique_names = set(
        counts[counts == 1].index
    )

    unique_players = players[
        players["normalized_name"]
        .isin(unique_names)
    ]

    return (
        unique_players
        .set_index("normalized_name")
        [
            [
                "player_id",
                "full_name",
            ]
        ]
        .to_dict("index")
    )


def build_alias_lookup(
    aliases: pd.DataFrame,
    players: pd.DataFrame,
    player_lookup: dict,
) -> dict:
    """Validate aliases and map source names to players."""
    alias_lookup = {}
    invalid_aliases = []

    players_by_id = (
        players
        .set_index("player_id")
        ["full_name"]
        .to_dict()
    )

    for row in aliases.itertuples():
        source = normalize_name(
            row.source_name
        )

        explicit_id = getattr(
            row,
            "player_id",
            None,
        )

        # Prefer an explicitly reviewed player ID.
        if pd.notna(explicit_id):
            explicit_id = int(explicit_id)

            full_name = players_by_id.get(
                explicit_id
            )

            if full_name is None:
                invalid_aliases.append(
                    (
                        row.source_name,
                        f"player_id={explicit_id}",
                    )
                )
                continue

            alias_lookup[source] = {
                "player_id": explicit_id,
                "full_name": full_name,
            }

            continue

        canonical = normalize_name(
            row.canonical_name
        )

        match = player_lookup.get(
            canonical
        )

        if match is None:
            invalid_aliases.append(
                (
                    row.source_name,
                    row.canonical_name,
                )
            )
            continue

        alias_lookup[source] = match

    print("\nAlias validation")
    print("----------------")
    print(
        f"Alias rows: {len(aliases):,}"
    )
    print(
        f"Valid aliases: "
        f"{len(alias_lookup):,}"
    )
    print(
        f"Invalid aliases: "
        f"{len(invalid_aliases):,}"
    )

    if invalid_aliases:
        print(
            "\nAliases requiring review:"
        )

        for source, target in invalid_aliases:
            print(
                f"- {source} -> {target}"
            )

    return alias_lookup

def resolve_players(
    assets: pd.DataFrame,
    player_lookup: dict,
    alias_lookup: dict,
) -> pd.DataFrame:
    """Resolve trade player assets using exact names then aliases."""
    assets = assets.copy()

    assets["player_id"] = pd.NA
    assets["matched_player_name"] = pd.NA
    assets["match_method"] = pd.NA

    player_mask = (
        assets["asset_type"]
        == "PLAYER_CANDIDATE"
    )

    assets.loc[
        player_mask,
        "normalized_name",
    ] = (
        assets.loc[
            player_mask,
            "asset_description",
        ]
        .apply(normalize_name)
    )

    for index in assets[
        player_mask
    ].index:
        normalized = assets.at[
            index,
            "normalized_name",
        ]

        # First try exact normalized match.
        match = player_lookup.get(
            normalized
        )

        method = "EXACT"

        # Then try reviewed aliases.
        if match is None:
            match = alias_lookup.get(
                normalized
            )

            method = "ALIAS"

        if match is not None:
            assets.at[
                index,
                "player_id",
            ] = match["player_id"]

            assets.at[
                index,
                "matched_player_name",
            ] = match["full_name"]

            assets.at[
                index,
                "match_method",
            ] = method

    return assets


def validate_resolution(
    assets: pd.DataFrame,
) -> None:
    """Report player identity-resolution coverage."""
    player_assets = assets[
        assets["asset_type"]
        == "PLAYER_CANDIDATE"
    ].copy()

    total = len(player_assets)

    exact = (
        player_assets["match_method"]
        .eq("EXACT")
        .sum()
    )

    alias = (
        player_assets["match_method"]
        .eq("ALIAS")
        .sum()
    )

    matched = (
        player_assets["player_id"]
        .notna()
        .sum()
    )

    unmatched = (
        player_assets["player_id"]
        .isna()
        .sum()
    )

    coverage = (
        matched / total * 100
        if total
        else 0
    )

    print("\nTrade Player Resolution")
    print("-----------------------")

    print(
        f"Player candidates: {total:,}"
    )

    print(
        f"Exact matches: {exact:,}"
    )

    print(
        f"Alias matches: {alias:,}"
    )

    print(
        f"Total matched: {matched:,}"
    )

    print(
        f"Unmatched: {unmatched:,}"
    )

    print(
        f"Match coverage: "
        f"{coverage:.2f}%"
    )

    if unmatched:
        unresolved = player_assets[
            player_assets[
                "player_id"
            ].isna()
        ]

        print(
            "\nMost common unmatched names:"
        )

        print(
            unresolved[
                "asset_description"
            ]
            .value_counts()
            .head(30)
            .to_string()
        )

        print(
            "\nUnique unmatched descriptions: "
            f"{unresolved['asset_description'].nunique()}"
        )


def save_resolved_assets(
    assets: pd.DataFrame,
) -> None:
    """Save resolved trade assets."""
    output = (
        PROCESSED_DATA_DIR
        / "trade_assets_resolved.csv"
    )

    assets.to_csv(
        output,
        index=False,
    )

    print(f"\nSaved {output}")


def main() -> None:
    engine = create_engine(
        DATABASE_URL
    )

    assets = load_assets()
    players = load_players(engine)
    aliases = load_aliases()

    player_lookup = (
        build_player_lookup(players)
    )

    alias_lookup = (
        build_alias_lookup(
            aliases,
            players,
            player_lookup,
        )
    )

    resolved = resolve_players(
        assets,
        player_lookup,
        alias_lookup,
    )

    validate_resolution(
        resolved
    )

    save_resolved_assets(
        resolved
    )

    engine.dispose()


if __name__ == "__main__":
    main()