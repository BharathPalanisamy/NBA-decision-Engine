import os
import time
import random
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


SEASONS = ["2025-26"]
SLEEP_MIN = 0.3
SLEEP_MAX = 0.7
MAX_WORKERS = 20  # Parallel requests

OUT_PATH = "data/raw/player_gamelogs.csv"
CHECKPOINT_PATH = "data/raw/_checkpoint_gamelogs.csv"
FAILED_PATH = "data/raw/_failed_players.csv"


def make_session() -> requests.Session:
    """
    NBA Stats endpoints often block default python requests.
    Use a session with browser-like headers + retries.
    """
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nba.com/",
        "Origin": "https://www.nba.com",
        "Connection": "keep-alive",
    })

    retry = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def sleep_jitter():
    time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))


def load_checkpoint() -> set[tuple[int, str]]:
    """
    Returns set of (player_id, season) already collected.
    """
    if not os.path.exists(CHECKPOINT_PATH):
        return set()
    df = pd.read_csv(CHECKPOINT_PATH, usecols=["player_id", "season"])
    return set(zip(df["player_id"].astype(int), df["season"].astype(str)))


def append_checkpoint(df: pd.DataFrame):
    header = not os.path.exists(CHECKPOINT_PATH)
    df.to_csv(CHECKPOINT_PATH, mode="a", header=header, index=False)


def log_failed(player_id: int, player_name: str, season: str, err: str):
    header = not os.path.exists(FAILED_PATH)
    pd.DataFrame([{
        "player_id": player_id,
        "player_name": player_name,
        "season": season,
        "error": err
    }]).to_csv(FAILED_PATH, mode="a", header=header, index=False)


def fetch_player_season(session: requests.Session, player_id: int, player_name: str, season: str) -> tuple:
    """
    Fetch one player's season gamelog. Returns (df, player_id, player_name, season, error)
    """
    try:
        sleep_jitter()
        gl = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season,
            timeout=30,
            headers=session.headers
        )
        df = gl.get_data_frames()[0]
        
        if df is None or df.empty:
            return (None, player_id, player_name, season, None)
        
        df["player_id"] = player_id
        df["player_name"] = player_name
        df["season"] = season
        
        return (df, player_id, player_name, season, None)
        
    except Exception as e:
        return (None, player_id, player_name, season, str(e))


def main():
    os.makedirs("data/raw", exist_ok=True)

    active = players.get_active_players()
    session = make_session()
    done = load_checkpoint()

    print(f"✅ Active players: {len(active)}")
    print(f"✅ Already in checkpoint: {len(done)} player-season pairs")

    for season in SEASONS:
        print(f"\n📅 Pulling {season} ...")

        # Filter players not yet done for this season
        todo = [(p, season) for p in active if (int(p["id"]), season) not in done]
        
        season_rows = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(fetch_player_season, session, int(p["id"]), p["full_name"], season): (p, season)
                for p, season in todo
            }
            
            for future in tqdm(as_completed(futures), total=len(todo), desc=f"Pulling {season} game logs"):
                df, pid, pname, seas, error = future.result()
                
                if error:
                    log_failed(pid, pname, seas, error)
                    continue
                
                if df is not None:
                    append_checkpoint(df)
                    season_rows += len(df)
                
                done.add((pid, seas))

        print(f"✅ Collected ~{season_rows:,} rows for {season}")

    if not os.path.exists(CHECKPOINT_PATH):
        raise RuntimeError("No checkpoint file was created. Still blocked.")

    out = pd.read_csv(CHECKPOINT_PATH)

    wanted = [
        "player_id", "player_name", "season",
        "GAME_DATE", "MATCHUP",
        "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV",
        "FG3M", "FG3A", "FGM", "FGA", "FTM", "FTA",
        "PLUS_MINUS", "PF"
    ]
    cols = [c for c in wanted if c in out.columns]
    out = out[cols].copy()

    rename_map = {
        "GAME_DATE": "game_date",
        "MATCHUP": "matchup",
        "MIN": "minutes",
        "PTS": "points",
        "REB": "rebounds",
        "AST": "assists",
        "STL": "steals",
        "BLK": "blocks",
        "TOV": "turnovers",
        "FG3M": "fg3m",
        "FG3A": "fg3a",
        "FGM": "fgm",
        "FGA": "fga",
        "FTM": "ftm",
        "FTA": "fta",
        "PLUS_MINUS": "plus_minus",
        "PF": "personal_fouls",
    }
    out = out.rename(columns=rename_map)

    out.to_csv(OUT_PATH, index=False)
    print(f"\n✅ Saved FINAL: {len(out):,} rows → {OUT_PATH}")
    if os.path.exists(FAILED_PATH):
        failed = pd.read_csv(FAILED_PATH)
        print(f"⚠️ Failed requests logged: {len(failed):,} → {FAILED_PATH}")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
 