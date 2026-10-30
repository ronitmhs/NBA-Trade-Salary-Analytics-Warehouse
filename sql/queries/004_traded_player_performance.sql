-- Traded player season-over-season performance analysis.
--
-- Compares a traded player's full-season production during
-- the trade season against their previous NBA season.
--
-- IMPORTANT:
-- player_season_stats contains full-season aggregates.
-- This is NOT an exact before/after trade-date comparison.
--
-- Players must have played at least 20 games in both seasons
-- to reduce small-sample distortions.


WITH player_history AS (
    SELECT
        pss.player_id,
        s.season_id,
        s.season,
        s.start_year,

        pss.games_played,
        pss.points,
        pss.rebounds,
        pss.assists,
        pss.steals,
        pss.blocks,

        (
            pss.points
            + pss.rebounds
            + pss.assists
            + pss.steals
            + pss.blocks
        ) AS production_score,

        LAG(
            pss.games_played
        ) OVER (
            PARTITION BY pss.player_id
            ORDER BY s.start_year
        ) AS previous_games_played,

        LAG(
            pss.points
        ) OVER (
            PARTITION BY pss.player_id
            ORDER BY s.start_year
        ) AS previous_points,

        LAG(
            pss.rebounds
        ) OVER (
            PARTITION BY pss.player_id
            ORDER BY s.start_year
        ) AS previous_rebounds,

        LAG(
            pss.assists
        ) OVER (
            PARTITION BY pss.player_id
            ORDER BY s.start_year
        ) AS previous_assists,

        LAG(
            (
                pss.points
                + pss.rebounds
                + pss.assists
                + pss.steals
                + pss.blocks
            )
        ) OVER (
            PARTITION BY pss.player_id
            ORDER BY s.start_year
        ) AS previous_production_score

    FROM player_season_stats pss

    JOIN seasons s
        ON pss.season_id = s.season_id
),


traded_players AS (
    SELECT DISTINCT
        ta.trade_id,
        ta.player_id,
        ta.receiving_team_id,
        tr.trade_date,
        tr.season_id AS trade_season_id

    FROM trade_assets ta

    JOIN trades tr
        ON ta.trade_id = tr.trade_id

    WHERE
        ta.asset_type = 'PLAYER_CANDIDATE'
        AND ta.player_id IS NOT NULL
),


trade_performance AS (
    SELECT
        tp.trade_id,
        tp.trade_date,

        p.player_id,
        p.full_name,

        t.full_name AS receiving_team,
        t.abbreviation AS receiving_team_abbreviation,

        ph.season AS trade_season,

        ph.previous_games_played,
        ph.games_played AS trade_season_games,

        ph.previous_points,
        ph.points AS trade_season_points,

        ph.previous_rebounds,
        ph.rebounds AS trade_season_rebounds,

        ph.previous_assists,
        ph.assists AS trade_season_assists,

        ph.previous_production_score,
        ph.production_score AS trade_season_production,

        (
            ph.production_score
            - ph.previous_production_score
        ) AS production_change,

        CASE
            WHEN ph.previous_production_score = 0
                THEN NULL

            ELSE (
                (
                    ph.production_score
                    - ph.previous_production_score
                )
                / ph.previous_production_score
            ) * 100
        END AS production_change_pct

    FROM traded_players tp

    JOIN players p
        ON tp.player_id = p.player_id

    JOIN teams t
        ON tp.receiving_team_id = t.team_id

    JOIN player_history ph
        ON tp.player_id = ph.player_id
        AND tp.trade_season_id = ph.season_id
)


SELECT
    trade_date,
    full_name,
    receiving_team,
    receiving_team_abbreviation,
    trade_season,

    previous_games_played,
    trade_season_games,

    ROUND(
        previous_points,
        1
    ) AS previous_points,

    ROUND(
        trade_season_points,
        1
    ) AS trade_season_points,

    ROUND(
        previous_rebounds,
        1
    ) AS previous_rebounds,

    ROUND(
        trade_season_rebounds,
        1
    ) AS trade_season_rebounds,

    ROUND(
        previous_assists,
        1
    ) AS previous_assists,

    ROUND(
        trade_season_assists,
        1
    ) AS trade_season_assists,

    ROUND(
        previous_production_score,
        1
    ) AS previous_production_score,

    ROUND(
        trade_season_production,
        1
    ) AS trade_season_production,

    ROUND(
        production_change,
        1
    ) AS production_change,

    ROUND(
        production_change_pct,
        1
    ) AS production_change_pct

FROM trade_performance

WHERE
    previous_production_score IS NOT NULL
    AND previous_games_played >= 20
    AND trade_season_games >= 20

ORDER BY
    production_change DESC

LIMIT 25;