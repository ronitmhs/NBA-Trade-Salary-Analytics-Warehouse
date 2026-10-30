-- Normalized NBA trade tables.

CREATE TABLE IF NOT EXISTS trades (
    trade_id BIGINT PRIMARY KEY,
    trade_date DATE NOT NULL,
    season_id SMALLINT NOT NULL,
    description TEXT,
    notes TEXT,

    CONSTRAINT fk_trade_season
        FOREIGN KEY (season_id)
        REFERENCES seasons(season_id)
);


CREATE TABLE IF NOT EXISTS trade_teams (
    trade_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,

    PRIMARY KEY (trade_id, team_id),

    CONSTRAINT fk_trade_team_trade
        FOREIGN KEY (trade_id)
        REFERENCES trades(trade_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_trade_team_team
        FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
);


CREATE TABLE IF NOT EXISTS trade_assets (
    trade_asset_id BIGSERIAL PRIMARY KEY,

    trade_id BIGINT NOT NULL,
    receiving_team_id BIGINT NOT NULL,

    asset_type VARCHAR(30) NOT NULL,
    asset_description TEXT NOT NULL,

    player_id BIGINT,
    player_match_method VARCHAR(20),

    CONSTRAINT fk_trade_asset_trade
        FOREIGN KEY (trade_id)
        REFERENCES trades(trade_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_trade_asset_team
        FOREIGN KEY (receiving_team_id)
        REFERENCES teams(team_id),

    CONSTRAINT fk_trade_asset_player
        FOREIGN KEY (player_id)
        REFERENCES players(player_id),

    CONSTRAINT trade_asset_type_check
        CHECK (
            asset_type IN (
                'PLAYER_CANDIDATE',
                'DRAFT_PICK',
                'DRAFT_RIGHTS',
                'PICK_SWAP',
                'CASH',
                'TRADE_EXCEPTION',
                'OTHER'
            )
        ),

    CONSTRAINT trade_player_match_method_check
        CHECK (
            player_match_method IS NULL
            OR player_match_method IN (
                'EXACT',
                'ALIAS'
            )
        )
);


CREATE INDEX IF NOT EXISTS idx_trades_date
    ON trades(trade_date);

CREATE INDEX IF NOT EXISTS idx_trades_season
    ON trades(season_id);

CREATE INDEX IF NOT EXISTS idx_trade_teams_team
    ON trade_teams(team_id);

CREATE INDEX IF NOT EXISTS idx_trade_assets_trade
    ON trade_assets(trade_id);

CREATE INDEX IF NOT EXISTS idx_trade_assets_team
    ON trade_assets(receiving_team_id);

CREATE INDEX IF NOT EXISTS idx_trade_assets_player
    ON trade_assets(player_id);

CREATE INDEX IF NOT EXISTS idx_trade_assets_type
    ON trade_assets(asset_type);