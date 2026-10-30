CREATE TABLE IF NOT EXISTS player_salaries (
    salary_id BIGSERIAL PRIMARY KEY,

    player_id BIGINT,
    team_id BIGINT NOT NULL,
    season_id SMALLINT NOT NULL,

    bbref_id VARCHAR(20),
    salary BIGINT NOT NULL,
    salary_cap BIGINT NOT NULL,
    luxury_tax BIGINT NOT NULL,

    salary_cap_pct NUMERIC(6,2),
    luxury_tax_pct NUMERIC(6,2),

    CONSTRAINT fk_salary_player
        FOREIGN KEY (player_id)
        REFERENCES players(player_id),

    CONSTRAINT fk_salary_team
        FOREIGN KEY (team_id)
        REFERENCES teams(team_id),

    CONSTRAINT fk_salary_season
        FOREIGN KEY (season_id)
        REFERENCES seasons(season_id),

    CONSTRAINT salary_positive_check
        CHECK (salary >= 0),

    CONSTRAINT salary_cap_positive_check
        CHECK (salary_cap > 0),

    CONSTRAINT luxury_tax_positive_check
        CHECK (luxury_tax > 0),

    CONSTRAINT salary_cap_pct_check
        CHECK (salary_cap_pct >= 0),

    CONSTRAINT luxury_tax_pct_check
        CHECK (luxury_tax_pct >= 0)
);


CREATE INDEX IF NOT EXISTS idx_salary_player
    ON player_salaries(player_id);

CREATE INDEX IF NOT EXISTS idx_salary_team
    ON player_salaries(team_id);

CREATE INDEX IF NOT EXISTS idx_salary_season
    ON player_salaries(season_id);

CREATE INDEX IF NOT EXISTS idx_salary_amount
    ON player_salaries(salary DESC);

CREATE INDEX IF NOT EXISTS idx_salary_cap_pct
    ON player_salaries(salary_cap_pct DESC);