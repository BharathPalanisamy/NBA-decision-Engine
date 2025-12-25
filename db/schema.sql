DROP TABLE IF EXISTS player_game_logs;

CREATE TABLE player_game_logs (
    id SERIAL PRIMARY KEY,
    player_id INTEGER,
    player_name TEXT,
    season TEXT,
    game_date DATE,
    matchup TEXT,
    minutes FLOAT,
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    fg3m INTEGER,
    fg3a INTEGER,
    fgm INTEGER,
    fga INTEGER,
    ftm INTEGER,
    fta INTEGER,
    plus_minus INTEGER,
    personal_fouls INTEGER
);

CREATE INDEX idx_player_game_logs_player
ON player_game_logs(player_id);

CREATE INDEX idx_player_game_logs_date
ON player_game_logs(game_date);

CREATE INDEX idx_player_game_logs_season
ON player_game_logs(season);
