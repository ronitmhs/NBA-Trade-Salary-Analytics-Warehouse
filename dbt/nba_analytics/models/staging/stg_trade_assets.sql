select
    trade_asset_id,
    trade_id,
    receiving_team_id,
    asset_type,
    asset_description,
    player_id,
    player_match_method

from {{ source('nba_warehouse', 'trade_assets') }}