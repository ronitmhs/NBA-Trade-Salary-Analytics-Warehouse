-- Trade acquisition value analysis.
--
-- Compares the salary and season-level production of players
-- acquired in trades.
--
-- Primary value metric:
--     production percentile - salary percentile
--
-- Positive value_gap means the player's production ranking
-- exceeded their salary ranking within that NBA season.
--
-- IMPORTANT:
-- Performance represents full-season statistics, not
-- post-trade-only performance.


WITH player_salary AS (
    SELECT
        player_id,
        season_id,

        SUM(salary) AS total_salary,
        MAX(salary_cap) AS salary_cap

    FROM player_salaries

    WHERE player_id IS NOT NULL

    GROUP BY
        player_id,
        season_id
),


acquired_players AS (
    SELECT DISTINCT
        tr.trade_id,
        tr.trade_date,
        tr.season_id,

        ta.receiving_team_id,
        ta.player_id

    FROM trades tr

    JOIN trade_assets ta
        ON tr.trade_id = ta.trade_id

    WHERE
        ta.asset_type = 'PLAYER_CANDIDATE'
        AND ta.player_id IS NOT NULL
),


player_trade_value AS (
    SELECT
        ap.trade_id,
        ap.trade_date,

        s.season,
        s.season_id,

        t.full_name AS receiving_team,
        t.abbreviation
            AS receiving_team_abbreviation,

        p.player_id,
        p.full_name AS player_name,

        ps.total_salary,
        ps.salary_cap,

        (
            ps.total_salary
            / ps.salary_cap::numeric
        ) * 100 AS salary_cap_pct,

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

    FROM acquired_players ap

    JOIN players p
        ON ap.player_id = p.player_id

    JOIN teams t
        ON ap.receiving_team_id = t.team_id

    JOIN seasons s
        ON ap.season_id = s.season_id

    JOIN player_salary ps
        ON ap.player_id = ps.player_id
        AND ap.season_id = ps.season_id

    JOIN player_season_stats stats
        ON ap.player_id = stats.player_id
        AND ap.season_id = stats.season_id

    WHERE
        ps.total_salary > 0
        AND stats.games_played >= 20
        AND (
            ps.total_salary
            / ps.salary_cap::numeric
        ) >= 0.01
),


percentile_metrics AS (
    SELECT
        *,

        PERCENT_RANK() OVER (
            PARTITION BY season_id
            ORDER BY total_salary
        ) AS salary_percentile,

        PERCENT_RANK() OVER (
            PARTITION BY season_id
            ORDER BY production_score
        ) AS production_percentile

    FROM player_trade_value
),


value_metrics AS (
    SELECT
        *,

        production_percentile
            - salary_percentile
            AS value_gap,

        production_score
            / NULLIF(
                total_salary / 1000000.0,
                0
            )
            AS production_per_million

    FROM percentile_metrics
)


SELECT
    trade_date,
    season,

    receiving_team,
    receiving_team_abbreviation,

    player_name,

    ROUND(
        total_salary / 1000000.0,
        2
    ) AS salary_millions,

    ROUND(
        salary_cap_pct,
        2
    ) AS salary_cap_pct,

    games_played,

    ROUND(
        points,
        1
    ) AS points,

    ROUND(
        rebounds,
        1
    ) AS rebounds,

    ROUND(
        assists,
        1
    ) AS assists,

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
    ) AS value_gap,

    ROUND(
        production_per_million,
        2
    ) AS production_per_million

FROM value_metrics

ORDER BY
    value_gap DESC,
    production_score DESC

LIMIT 30;