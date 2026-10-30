with team_payroll as (

    select
        team_id,
        season_id,

        sum(salary) as total_payroll,
        max(salary_cap) as salary_cap

    from {{ ref('stg_player_salaries') }}

    group by
        team_id,
        season_id

),

team_performance as (

    select
        team_id,
        season_id,
        games_played,
        wins,
        losses,
        win_pct

    from {{ ref('stg_team_season_stats') }}

),

combined as (

    select
        payroll.team_id,
        payroll.season_id,

        teams.full_name as team_name,
        teams.abbreviation,

        seasons.season,

        payroll.total_payroll,
        payroll.salary_cap,

        (
            payroll.total_payroll
            / nullif(
                payroll.salary_cap::numeric,
                0
            )
        ) * 100 as payroll_pct_of_cap,

        performance.games_played,
        performance.wins,
        performance.losses,
        performance.win_pct,

        payroll.total_payroll
            / nullif(
                performance.wins,
                0
            ) as payroll_per_win

    from team_payroll payroll

    inner join team_performance performance
        on payroll.team_id = performance.team_id
        and payroll.season_id = performance.season_id

    inner join {{ ref('stg_teams') }} teams
        on payroll.team_id = teams.team_id

    inner join {{ ref('stg_seasons') }} seasons
        on payroll.season_id = seasons.season_id

),

rankings as (

    select
        *,

        rank() over (
            partition by season_id
            order by total_payroll desc
        ) as payroll_rank,

        rank() over (
            partition by season_id
            order by wins desc
        ) as wins_rank,

        rank() over (
            partition by season_id
            order by payroll_per_win
        ) as efficiency_rank

    from combined

)

select
    team_id,
    season_id,

    team_name,
    abbreviation,
    season,

    total_payroll,

    round(
        total_payroll / 1000000.0,
        2
    ) as payroll_millions,

    salary_cap,

    round(
        payroll_pct_of_cap,
        2
    ) as payroll_pct_of_cap,

    games_played,
    wins,
    losses,
    win_pct,

    round(
        payroll_per_win / 1000000.0,
        2
    ) as payroll_per_win_millions,

    payroll_rank,
    wins_rank,
    efficiency_rank

from rankings