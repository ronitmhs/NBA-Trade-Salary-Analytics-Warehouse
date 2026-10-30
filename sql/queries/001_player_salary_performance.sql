-- Player salary and performance analysis
-- Combines salary facts with season-level player performance.

WITH player_salary_performance AS (
    SELECT
        s.season,
        p.player_id,
        p.full_name,
        ps.salary,
        ps.salary_cap,
        ps.salary_cap_pct,

        stats.games_played,
        stats.minutes,
        stats.points,
        stats.rebounds,
        stats.assists,
        stats.steals,
        stats.blocks,
        stats.turnovers,
        stats.plus_minus

    FROM player_salaries ps

    JOIN players p
        ON ps.player_id = p.player_id

    JOIN seasons s
        ON ps.season_id = s.season_id

    JOIN player_season_stats stats
        ON ps.player_id = stats.player_id
        AND ps.season_id = stats.season_id

    WHERE
        ps.salary > 0
        AND stats.games_played >= 20
)

SELECT
    season,
    full_name,
    salary,
    salary_cap_pct,
    games_played,
    points,
    rebounds,
    assists,
    plus_minus

FROM player_salary_performance

ORDER BY
    season DESC,
    salary DESC;