select
    salary_id,
    player_id,
    team_id,
    season_id,
    bbref_id,
    salary,
    salary_cap,
    luxury_tax,
    salary_cap_pct,
    luxury_tax_pct

from {{ source('nba_warehouse', 'player_salaries') }}