import statsapi
import json
import time
from datetime import datetime, timedelta
import re
import psycopg2

def clean_final_score_keys(raw_json):
    if 'final_score' in raw_json:
        fixed = {}
        for k, v in raw_json['final_score'].items():
            match = re.search(r"\d+", k)
            if match:
                fixed[match.group()] = v
        raw_json['final_score'] = fixed
    return raw_json

def main():
    # Set the date (use today or hardcode for testing)
    today = (datetime.now() - timedelta(days=1)).date()
    
    # Prepare container for results
    all_games = []
    
    # Get game schedule
    schedule = statsapi.schedule(date=today)
    
    # Valid game statuses to include
    valid_statuses = [
        'final', 'game over', 'completed early: rain', 'completed early', 'completed'
    ]
    
    print(f"📅 Raw schedule for {today} has {len(schedule)} entries")
    for i, game in enumerate(schedule):
        print(f"{i+1}. {game.get('summary', 'No summary')} | status: {game.get('status')}")
    
    
    for game in schedule:
        status = game.get('status', '').strip().lower()
        
        if status not in valid_statuses:
            print(f"⛔ Skipping game: {game.get('summary')} | status: {status}")
            continue
    
        game_id = game['game_id']
    
        # Add delay and fetch boxscore
        time.sleep(1)
        box = statsapi.boxscore_data(game_id)
    
        if not box:
            print(f"❌ No boxscore for {game_id} — skipping.")
            continue
    
        # Now safe to access 'box'
        away_team = box['away']['team']
        home_team = box['home']['team']
        away_score = box['away']['teamStats']['batting']['runs']
        home_score = box['home']['teamStats']['batting']['runs']
    
        print(f"\n▶️ Processing: {away_team} @ {home_team} (Game ID: {game_id})")
    
        # Add delay to avoid hitting rate limits
        time.sleep(1)
    
        box = statsapi.boxscore_data(game_id)
        
        if not box:
            print(f"❌ No boxscore for {game_id} — skipping.")
            continue
    
        print(f"✅ Got boxscore for {game_id} — adding to results.")
    
        linescore = box.get('linescore', {})
        innings = linescore.get('innings', [])
        away_1st = 0
        home_1st = 0
        for inning in innings:
            if inning.get("num") == 1:
                away_1st = inning.get("away", 0)
                home_1st = inning.get("home", 0)
                break
    
        game_data = {
            "game_id": game_id,
            "date": today,
            "away_team": away_team,
            "home_team": home_team,
            "final_score": {
                str(away_team): away_score,
                str(home_team): home_score
            },
            "first_inning_runs": {
                str(away_team): away_1st,
                str(home_team): home_1st
            },
            "away_batters": box.get('awayBatters', []),
            "home_batters": box.get('homeBatters', []),
            "away_pitchers": box.get('awayPitchers', []),
            "home_pitchers": box.get('homePitchers', [])
        }
    
        game_data = clean_final_score_keys(game_data)
        all_games.append(game_data)
    
    ## Save to JSON formatted table
    output_filename = "mlb_box_scores.jsonl"
    with open(output_filename, "w", encoding="utf-8") as f:
        for game in all_games:
            f.write(json.dumps(game, ensure_ascii=False, default=str) + "\n")
    
    # Insert into PostgreSQL
    conn = psycopg2.connect("your_connection_string_here")  # Replace with your actual connection string
    cur = conn.cursor()
    
    with open("mlb_box_scores.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            cur.execute("INSERT INTO json_mlb (raw_json) VALUES (%s)", [json.loads(line)])
    
    conn.commit()
    cur.close()
    conn.close()
    
    
if __name__ == "__main__":
    main()
    
