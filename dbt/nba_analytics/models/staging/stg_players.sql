select
    player_id,
    full_name,
    first_name,
    last_name,
    is_active

from {{ source('nba_warehouse', 'players') }}