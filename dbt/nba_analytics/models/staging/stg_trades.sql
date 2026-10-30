select
    trade_id,
    trade_date,
    season_id,
    description,
    notes

from {{ source('nba_warehouse', 'trades') }}