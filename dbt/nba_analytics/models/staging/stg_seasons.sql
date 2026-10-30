select
    season_id,
    season,
    start_year,
    end_year

from {{ source('nba_warehouse', 'seasons') }}