-- Core dimension tables for the NBA analytics warehouse.

CREATE TABLE IF NOT EXISTS players (
    player_id BIGINT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT FALSE
);


CREATE TABLE IF NOT EXISTS teams (
    team_id BIGINT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(5) NOT NULL,
    nickname VARCHAR(50),
    city VARCHAR(50),
    state VARCHAR(50),
    year_founded SMALLINT,

    CONSTRAINT teams_abbreviation_unique
        UNIQUE (abbreviation),

    CONSTRAINT teams_year_founded_check
        CHECK (year_founded >= 1946)
);


CREATE TABLE IF NOT EXISTS seasons (
    season_id SMALLSERIAL PRIMARY KEY,
    season VARCHAR(7) NOT NULL UNIQUE,
    start_year SMALLINT NOT NULL,
    end_year SMALLINT NOT NULL,

    CONSTRAINT seasons_year_check
        CHECK (end_year = start_year + 1),

    CONSTRAINT seasons_format_check
        CHECK (season ~ '^[0-9]{4}-[0-9]{2}$')
);