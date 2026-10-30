with acquired_players as (

    select distinct
        trades.trade_id,
        trades.trade_date,
        trades.season_id,

        assets.receiving_team_id,
        assets.player_id

    from {{ ref('stg_trades') }} trades

    inner join {{ ref('stg_trade_assets') }} assets
        on trades.trade_id = assets.trade_id

    where
        assets.asset_type = 'PLAYER_CANDIDATE'
        and assets.player_id is not null

),

trade_value as (

    select
        acquired.trade_id,
        acquired.trade_date,

        acquired.player_id,
        acquired.receiving_team_id,
        acquired.season_id,

        seasons.season,

        teams.full_name as receiving_team,
        teams.abbreviation
            as receiving_team_abbreviation,

        players.full_name as player_name,

        value.games_played,
        value.points,
        value.rebounds,
        value.assists,
        value.steals,
        value.blocks,

        value.production_score,

        value.total_salary,
        value.salary_cap,
        value.salary_cap_pct

    from acquired_players acquired

    inner join {{ ref('int_player_season_value') }} value
        on acquired.player_id = value.player_id
        and acquired.season_id = value.season_id

    inner join {{ ref('stg_players') }} players
        on acquired.player_id = players.player_id

    inner join {{ ref('stg_teams') }} teams
        on acquired.receiving_team_id = teams.team_id

    inner join {{ ref('stg_seasons') }} seasons
        on acquired.season_id = seasons.season_id

    where
        value.games_played >= 20
        and value.total_salary > 0
        and value.salary_cap_pct >= 1

),

percentiles as (

    select
        *,

        percent_rank() over (
            partition by season_id
            order by total_salary
        ) as salary_percentile,

        percent_rank() over (
            partition by season_id
            order by production_score
        ) as production_percentile

    from trade_value

),

final as (

    select
        *,

        production_percentile
            - salary_percentile
            as value_gap,

        production_score
            / nullif(
                total_salary / 1000000.0,
                0
            )
            as production_per_million

    from percentiles

)

select
    trade_id,
    trade_date,

    player_id,
    receiving_team_id,
    season_id,

    season,

    receiving_team,
    receiving_team_abbreviation,

    player_name,

    games_played,

    points,
    rebounds,
    assists,
    steals,
    blocks,

    production_score,

    total_salary,

    round(
        total_salary / 1000000.0,
        2
    ) as salary_millions,

    salary_cap,

    round(
        salary_cap_pct,
        2
    ) as salary_cap_pct,

    salary_percentile,
    production_percentile,
    value_gap,

    round(
        production_per_million,
        2
    ) as production_per_million

from final