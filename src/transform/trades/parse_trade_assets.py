from pathlib import Path
import re

import pandas as pd


PROCESSED_DATA_DIR = Path("data/processed")

TRADES_FILE = (
    PROCESSED_DATA_DIR / "trades_normalized.csv"
)

TRADE_TEAMS_FILE = (
    PROCESSED_DATA_DIR / "trade_teams_mapped.csv"
)


def load_data():
    """Load normalized trade data."""
    trades = pd.read_csv(TRADES_FILE)

    trade_teams = pd.read_csv(
        TRADE_TEAMS_FILE
    )

    return trades, trade_teams


def classify_asset(asset: str) -> str:
    """Conservatively classify a trade asset."""
    text = asset.lower().strip()

    # Empty or placeholder values.
    if not text or text == "—":
        return "OTHER"

    # Cash.
    if "cash" in text:
        return "CASH"

    # Trade exceptions / exemptions.
    if (
        "trade exception" in text
        or "traded player exception" in text
        or "exemption" in text
    ):
        return "TRADE_EXCEPTION"

    # Pick swaps.
    if "swap" in text:
        return "PICK_SWAP"

    # Draft picks and pick-related fragments.
    if (
        "pick" in text
        or "protected top" in text
        or "protected #" in text
        or "draft considerations" in text
        or "protections removed" in text
    ):
        return "DRAFT_PICK"

    # Draft rights.
    if (
        "rights to" in text
        or text.startswith("rights ")
    ):
        return "DRAFT_RIGHTS"

    # Fragments produced by complex trade descriptions.
    if (
        text.startswith("from ")
        or text.startswith("protected ")
        or "not exercised" in text
        or ") with " in text
    ):
        return "OTHER"

    # Team-name fragments that are not player assets.
    if text in {
        "heat",
        "magic",
    }:
        return "OTHER"

    # Anything remaining may be a player.
    return "PLAYER_CANDIDATE"


def parse_team_sections(
    trade_id: int,
    notes: str,
) -> list[dict]:
    """Parse acquired assets for each team in a trade."""
    records = []

    sections = [
        section.strip()
        for section in notes.split("|")
        if section.strip()
    ]

    for section in sections:
        match = re.match(
            r"^([A-Z]{2,3}) acquired:\s*(.*?)(?:;\s*sent:|$)",
            section,
        )

        if not match:
            continue

        team = match.group(1).strip()
        acquired_text = match.group(2).strip()

        assets = [
            asset.strip()
            for asset in acquired_text.split(";")
            if asset.strip()
        ]

        for asset in assets:
            records.append(
                {
                    "trade_id": trade_id,
                    "team_abbreviation": team,
                    "asset_description": asset,
                    "asset_type": classify_asset(
                        asset
                    ),
                }
            )

    return records


def parse_assets(
    trades: pd.DataFrame,
) -> pd.DataFrame:
    """Parse all acquired assets from all trades."""
    records = []

    for row in trades.itertuples():
        parsed = parse_team_sections(
            row.trade_id,
            row.notes,
        )

        records.extend(parsed)

    return pd.DataFrame(records)


def map_team_ids(
    assets: pd.DataFrame,
    trade_teams: pd.DataFrame,
) -> pd.DataFrame:
    """Attach NBA team IDs to each acquired asset."""
    team_lookup = (
        trade_teams[
            [
                "trade_id",
                "team_id",
                "team_abbreviation",
            ]
        ]
        .drop_duplicates()
    )

    return assets.merge(
        team_lookup,
        how="left",
        on=[
            "trade_id",
            "team_abbreviation",
        ],
        validate="many_to_one",
    )


def validate_assets(
    assets: pd.DataFrame,
) -> None:
    """Validate parsed trade assets."""
    print("\nTrade Asset Parsing")
    print("-------------------")

    print(
        f"Parsed assets: {len(assets):,}"
    )

    print(
        f"Trades with parsed assets: "
        f"{assets['trade_id'].nunique():,}"
    )

    print(
        f"Mapped team IDs: "
        f"{assets['team_id'].notna().sum():,}"
    )

    print(
        f"Unmapped team IDs: "
        f"{assets['team_id'].isna().sum():,}"
    )

    print("\nAsset types:")

    print(
        assets["asset_type"]
        .value_counts()
        .to_string()
    )

    print("\nSample assets:")

    print(
        assets[
            [
                "trade_id",
                "team_abbreviation",
                "asset_type",
                "asset_description",
            ]
        ]
        .head(25)
        .to_string(index=False)
    )


def save_assets(
    assets: pd.DataFrame,
) -> None:
    """Save parsed trade assets."""
    output = (
        PROCESSED_DATA_DIR
        / "trade_assets_parsed.csv"
    )

    assets.to_csv(
        output,
        index=False,
    )

    print(f"\nSaved {output}")


def main() -> None:
    trades, trade_teams = load_data()

    assets = parse_assets(trades)

    assets = map_team_ids(
        assets,
        trade_teams,
    )

    validate_assets(assets)

    if assets["team_id"].isna().any():
        raise SystemExit(
            "Some trade assets could not "
            "be mapped to an NBA team."
        )

    save_assets(assets)


if __name__ == "__main__":
    main()