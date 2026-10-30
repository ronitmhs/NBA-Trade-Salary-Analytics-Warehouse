-- Team payroll efficiency analysis
-- Compares team payroll spending with regular-season performance.

WITH team_payroll AS (
    SELECT
        team_id,
        season_id,
        SUM(salary) AS total_payroll
    FROM player_salaries
    GROUP BY
        team_id,
        season_id
),

team_financials AS (
    SELECT
        tp.team_id,
        tp.season_id,
        tp.total_payroll,

        MAX(ps.salary_cap) AS salary_cap,

        tp.total_payroll
            / MAX(ps.salary_cap)::numeric
            AS payroll_to_cap_ratio

    FROM team_payroll tp

    JOIN player_salaries ps
        ON tp.team_id = ps.team_id
        AND tp.season_id = ps.season_id

    GROUP BY
        tp.team_id,
        tp.season_id,
        tp.total_payroll
),

team_analysis AS (
    SELECT
        s.season,
        s.season_id,
        t.full_name AS team_name,
        t.abbreviation,

        tf.total_payroll,
        tf.salary_cap,
        tf.payroll_to_cap_ratio,

        stats.wins,
        stats.losses,
        stats.win_pct,

        tf.total_payroll
            / NULLIF(stats.wins, 0)
            AS payroll_per_win

    FROM team_financials tf

    JOIN teams t
        ON tf.team_id = t.team_id

    JOIN seasons s
        ON tf.season_id = s.season_id

    JOIN team_season_stats stats
        ON tf.team_id = stats.team_id
        AND tf.season_id = stats.season_id
),

rankings AS (
    SELECT
        *,

        RANK() OVER (
            PARTITION BY season_id
            ORDER BY total_payroll DESC
        ) AS payroll_rank,

        RANK() OVER (
            PARTITION BY season_id
            ORDER BY wins DESC
        ) AS wins_rank,

        RANK() OVER (
            PARTITION BY season_id
            ORDER BY payroll_per_win
        ) AS efficiency_rank

    FROM team_analysis
)

SELECT
    season,
    team_name,
    abbreviation,

    total_payroll,

    ROUND(
        payroll_to_cap_ratio * 100,
        2
    ) AS payroll_pct_of_cap,

    wins,
    losses,

    ROUND(
        win_pct,
        3
    ) AS win_pct,

    ROUND(
        payroll_per_win / 1000000,
        2
    ) AS payroll_per_win_millions,

    payroll_rank,
    wins_rank,
    efficiency_rank

FROM rankings

WHERE season = '2025-26'

ORDER BY efficiency_rank;