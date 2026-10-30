WITH player_salary AS (
    SELECT
        player_id,
        season_id,
        SUM(salary) AS total_salary,
        SUM(salary) / MAX(salary_cap)::numeric * 100
            AS salary_cap_pct
    FROM player_salaries
    WHERE
        player_id IS NOT NULL
        AND salary > 0
    GROUP BY
        player_id,
        season_id
),

player_data AS (
    SELECT
        s.season,
        s.season_id,
        p.player_id,
        p.full_name,

        ps.total_salary AS salary,
        ps.salary_cap_pct,

        stats.games_played,
        stats.points,
        stats.rebounds,
        stats.assists,
        stats.steals,
        stats.blocks,

        (
            stats.points
            + stats.rebounds
            + stats.assists
            + stats.steals
            + stats.blocks
        ) AS production_score

    FROM player_salary ps

    JOIN players p
        ON ps.player_id = p.player_id

    JOIN seasons s
        ON ps.season_id = s.season_id

    JOIN player_season_stats stats
        ON ps.player_id = stats.player_id
        AND ps.season_id = stats.season_id

    WHERE stats.games_played >= 20
),

percentiles AS (
    SELECT
        *,

        PERCENT_RANK() OVER (
            PARTITION BY season_id
            ORDER BY salary
        ) AS salary_percentile,

        PERCENT_RANK() OVER (
            PARTITION BY season_id
            ORDER BY production_score
        ) AS production_percentile

    FROM player_data
),

value_analysis AS (
    SELECT
        *,
        production_percentile
            - salary_percentile AS value_gap

    FROM percentiles
)

SELECT
    season,
    full_name,

    salary,

    ROUND(
        salary_cap_pct,
        2
    ) AS salary_cap_pct,

    games_played,

    ROUND(points, 1) AS points,
    ROUND(rebounds, 1) AS rebounds,
    ROUND(assists, 1) AS assists,

    ROUND(
        production_score,
        1
    ) AS production_score,

    ROUND(
        salary_percentile::numeric,
        3
    ) AS salary_percentile,

    ROUND(
        production_percentile::numeric,
        3
    ) AS production_percentile,

    ROUND(
        value_gap::numeric,
        3
    ) AS value_gap

FROM value_analysis

WHERE season = '2025-26'

ORDER BY value_gap DESC

LIMIT 25;