import requests
import pandas as pd

def get_nba_injury_report():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Failed to fetch injuries, status code: {resp.status_code}")
        return pd.DataFrame()
    
    data = resp.json()
    all_injuries = []

    for team in data.get("injuries", []):
        team_name = team.get("displayName")
        for injury in team.get("injuries", []):
            athlete = injury.get("athlete", {})
            all_injuries.append({
                "player_name": athlete.get("displayName"),
                "team_name": team_name,
                "status": injury.get("status"),
                "short_comment": injury.get("shortComment"),
                "long_comment": injury.get("longComment"),
                "return_date": injury.get("date")
            })
    
    df = pd.DataFrame(all_injuries)
    return df

if __name__ == "__main__":
    df = get_nba_injury_report()
    if df.empty:
        print("No injury data found.")
    else:
        print(df)
import requests
import pandas as pd

def get_nba_injury_report():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Failed to fetch injuries, status code: {resp.status_code}")
        return pd.DataFrame()
    
    data = resp.json()
    all_injuries = []

    for team in data.get("injuries", []):
        team_name = team.get("displayName")
        for injury in team.get("injuries", []):
            athlete = injury.get("athlete", {})
            all_injuries.append({
                "player_name": athlete.get("displayName"),
                "team_name": team_name,
                "status": injury.get("status"),
                "short_comment": injury.get("shortComment"),
                "long_comment": injury.get("longComment"),
                "return_date": injury.get("date")
            })
    
    df = pd.DataFrame(all_injuries)
    return df

if __name__ == "__main__":
    df = get_nba_injury_report()
    if df.empty:
        print("No injury data found.")
    else:
        print(df)
