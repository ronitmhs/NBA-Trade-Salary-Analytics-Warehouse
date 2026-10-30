select
    team_id,
    full_name,
    abbreviation,
    nickname,
    city,
    state,
    year_founded

from {{ source('nba_warehouse', 'teams') }}