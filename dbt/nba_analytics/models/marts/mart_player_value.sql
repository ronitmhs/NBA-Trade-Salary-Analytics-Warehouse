with player_value as (

    select
        v.player_id,
        v.season_id,

        p.full_name as player_name,

        s.season,

        v.games_played,
        v.points,
        v.rebounds,
        v.assists,
        v.steals,
        v.blocks,
        v.plus_minus,

        v.production_score,

        v.total_salary,
        v.salary_cap,
        v.salary_cap_pct

    from {{ ref('int_player_season_value') }} v

    inner join {{ ref('stg_players') }} p
        on v.player_id = p.player_id

    inner join {{ ref('stg_seasons') }} s
        on v.season_id = s.season_id

    where
        v.games_played >= 20
        and v.total_salary > 0

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

    from player_value

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
    player_id,
    season_id,
    player_name,
    season,

    games_played,

    points,
    rebounds,
    assists,
    steals,
    blocks,
    plus_minus,

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