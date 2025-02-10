import pandas as pd
import datetime as dt
from typing import Dict, Any
from footballmodels.opta.event_type import EventType
from dbconnect.connector import Connection
from functools import wraps
from hashlib import sha256

class TimedCache:
    def __init__(self, timeout: int):
        self.cache = {}
        self.timeout = timeout

    def __call__(self, func):
        @wraps(func)
        def wrapper(config: Dict[str, Any]):
            key = sha256(str(config).encode()).hexdigest()
            if key in self.cache:
                if dt.datetime.now() - self.cache[key]["time"] < dt.timedelta(seconds=self.timeout):
                    return self.cache[key]["data"]
            data = func(config)
            self.cache[key] = {"data": data, "time": dt.datetime.now()}
            return data

        return wrapper

@TimedCache(60*5)
def get_player_pass_data(config: Dict[str, Any]) -> pd.DataFrame:
    comp_str = ",".join(f"'{s}'" for s in config["competitions"])
    team = config["team"]
    if "opponents" in config:
        
        opponents_str = ",".join(f"'{s}'" for s in config["opponents"])
    query = f"""
    SELECT whoscored.*, mclachbot_leagues.decorated_name as dln, mclachbot_teams.decorated_name as dtn,
    player_sportsdb_links.date_of_birth as date_of_birth,
    gs.game_state, 
    eei.position
    FROM whoscored
    JOIN mclachbot_teams ON whoscored.team = mclachbot_teams.ws_team_name
    JOIN mclachbot_leagues ON whoscored.competition = mclachbot_leagues.ws_league_name
    JOIN player_sportsdb_links ON whoscored.playerId = player_sportsdb_links.ws_id
    JOIN derived.whoscored_game_state AS gs ON whoscored.id=gs.id
    JOIN derived.whoscored_extra_event_info AS eei ON whoscored.id=eei.id
    WHERE playerId={config['player_id']}

    AND competition IN ({comp_str})
    AND team='{team}'
    AND event_type IN (1, 18, 19)
    AND match_date >= '{config['start_date']}'
    AND match_date <= '{config['end_date']}'
    """
    if "opponents" in config:
        query += f"""
    AND opponent IN ({opponents_str})
    """
    conn = Connection(config["db_password"])
    data = conn.query(query, event_type_handler=lambda x: EventType(x))
    data["age"] = (pd.to_datetime(data['match_date']).max() - pd.to_datetime(data["date_of_birth"])).dt.days // 365
    data["age"] = data["age"].fillna(0)
    match_ids_str = ",".join(map(str, data["matchId"].unique()))
    query = f"""
        SELECT matchId,period, max(minute) as max_minute FROM whoscored
        WHERE matchId in (
            {match_ids_str}
        ) 
        GROUP BY matchId,period
    """
    match_period_data = conn.query(query)
    data = pd.merge(
        data, match_period_data, left_on=["matchId", "period"], right_on=["matchId", "period"]
    )
    return data
