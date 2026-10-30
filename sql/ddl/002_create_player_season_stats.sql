CREATE TABLE IF NOT EXISTS player_season_stats (
    player_season_stat_id BIGSERIAL PRIMARY KEY,

    player_id BIGINT NOT NULL,
    season_id SMALLINT NOT NULL,

    age NUMERIC(4,1),
    games_played SMALLINT NOT NULL,
    wins SMALLINT,
    losses SMALLINT,
    win_pct NUMERIC(5,4),

    minutes NUMERIC(6,2),

    field_goals_made NUMERIC(6,2),
    field_goals_attempted NUMERIC(6,2),
    field_goal_pct NUMERIC(5,4),

    three_pointers_made NUMERIC(6,2),
    three_pointers_attempted NUMERIC(6,2),
    three_point_pct NUMERIC(5,4),

    free_throws_made NUMERIC(6,2),
    free_throws_attempted NUMERIC(6,2),
    free_throw_pct NUMERIC(5,4),

    offensive_rebounds NUMERIC(6,2),
    defensive_rebounds NUMERIC(6,2),
    rebounds NUMERIC(6,2),

    assists NUMERIC(6,2),
    turnovers NUMERIC(6,2),
    steals NUMERIC(6,2),
    blocks NUMERIC(6,2),

    points NUMERIC(6,2),
    plus_minus NUMERIC(7,2),

    team_count SMALLINT NOT NULL DEFAULT 1,

    CONSTRAINT fk_player_stats_player
        FOREIGN KEY (player_id)
        REFERENCES players(player_id),

    CONSTRAINT fk_player_stats_season
        FOREIGN KEY (season_id)
        REFERENCES seasons(season_id),

    CONSTRAINT player_season_unique
        UNIQUE (player_id, season_id),

    CONSTRAINT player_stats_games_check
        CHECK (games_played >= 0),

    CONSTRAINT player_stats_team_count_check
        CHECK (team_count >= 1),

    CONSTRAINT player_stats_points_check
        CHECK (points >= 0)
);



CREATE INDEX IF NOT EXISTS idx_player_stats_player
    ON player_season_stats(player_id);

CREATE INDEX IF NOT EXISTS idx_player_stats_season
    ON player_season_stats(season_id);

CREATE INDEX IF NOT EXISTS idx_player_stats_points
    ON player_season_stats(points DESC);