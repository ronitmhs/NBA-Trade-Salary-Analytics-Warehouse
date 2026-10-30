CREATE TABLE IF NOT EXISTS team_season_stats (
    team_season_stat_id BIGSERIAL PRIMARY KEY,

    team_id BIGINT NOT NULL,
    season_id SMALLINT NOT NULL,

    games_played SMALLINT NOT NULL,
    wins SMALLINT NOT NULL,
    losses SMALLINT NOT NULL,
    win_pct NUMERIC(5,4),

    minutes NUMERIC(7,2),

    field_goals_made NUMERIC(7,2),
    field_goals_attempted NUMERIC(7,2),
    field_goal_pct NUMERIC(5,4),

    three_pointers_made NUMERIC(7,2),
    three_pointers_attempted NUMERIC(7,2),
    three_point_pct NUMERIC(5,4),

    free_throws_made NUMERIC(7,2),
    free_throws_attempted NUMERIC(7,2),
    free_throw_pct NUMERIC(5,4),

    offensive_rebounds NUMERIC(7,2),
    defensive_rebounds NUMERIC(7,2),
    rebounds NUMERIC(7,2),

    assists NUMERIC(7,2),
    turnovers NUMERIC(7,2),
    steals NUMERIC(7,2),
    blocks NUMERIC(7,2),

    points NUMERIC(7,2),
    plus_minus NUMERIC(7,2),

    CONSTRAINT fk_team_stats_team
        FOREIGN KEY (team_id)
        REFERENCES teams(team_id),

    CONSTRAINT fk_team_stats_season
        FOREIGN KEY (season_id)
        REFERENCES seasons(season_id),

    CONSTRAINT team_season_unique
        UNIQUE (team_id, season_id),

    CONSTRAINT team_stats_games_check
        CHECK (games_played >= 0),

    CONSTRAINT team_stats_record_check
        CHECK (wins + losses = games_played),

    CONSTRAINT team_stats_points_check
        CHECK (points >= 0)
);


CREATE INDEX IF NOT EXISTS idx_team_stats_team
    ON team_season_stats(team_id);

CREATE INDEX IF NOT EXISTS idx_team_stats_season
    ON team_season_stats(season_id);

CREATE INDEX IF NOT EXISTS idx_team_stats_win_pct
    ON team_season_stats(win_pct DESC);