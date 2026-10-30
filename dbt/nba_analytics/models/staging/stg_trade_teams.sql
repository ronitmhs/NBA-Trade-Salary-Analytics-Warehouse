select
    trade_id,
    team_id

from {{ source('nba_warehouse', 'trade_teams') }}