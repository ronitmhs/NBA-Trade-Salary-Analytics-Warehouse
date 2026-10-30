with player_salary as (

    select
        player_id,
        season_id,

        sum(salary) as total_salary,
        max(salary_cap) as salary_cap,
        max(luxury_tax) as luxury_tax

    from {{ ref('stg_player_salaries') }}

    where player_id is not null

    group by
        player_id,
        season_id

),

player_performance as (

    select
        player_id,
        season_id,
        games_played,
        points,
        rebounds,
        assists,
        steals,
        blocks,
        plus_minus,

        (
            points
            + rebounds
            + assists
            + steals
            + blocks
        ) as production_score

    from {{ ref('stg_player_season_stats') }}

),

combined as (

    select
        perf.player_id,
        perf.season_id,

        perf.games_played,
        perf.points,
        perf.rebounds,
        perf.assists,
        perf.steals,
        perf.blocks,
        perf.plus_minus,
        perf.production_score,

        salary.total_salary,
        salary.salary_cap,
        salary.luxury_tax,

        (
            salary.total_salary
            / nullif(
                salary.salary_cap::numeric,
                0
            )
        ) * 100 as salary_cap_pct

    from player_performance perf

    inner join player_salary salary
        on perf.player_id = salary.player_id
        and perf.season_id = salary.season_id

)

select *
from combined