# formula1/predictor.py

import datetime
import random
import fastf1
import pandas as pd
import warnings
import json
import os

# 1. Suppress the specific Pandas FutureWarning about timezone compatibility.
#    This is a known issue and this line will hide the noisy warning.
warnings.simplefilter(action='ignore', category=FutureWarning)

# 2. Tell the fastf1 library to only show log messages if they are 'WARNING' or worse.
#    This will hide all the "INFO: Using cached data..." messages.
fastf1.set_log_level('WARNING')

# Create the cache folder if it doesn't exist
CACHE_DIR = 'cache_folder'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Suppress noisy fastf1 cache warnings and use our created directory
fastf1.Cache.enable_cache(CACHE_DIR)

# A little bit of circuit flavor text
CIRCUIT_TIDBITS = {
    "Bahrain": "Known for its abrasive surface, tire degradation is always a key factor.",
    "Jeddah": "A high-speed street circuit. Expect close walls and high drama.",
    "Melbourne": "A fan favorite to start the season. It's a tricky, bumpy track.",
    "Imola": "An old-school, unforgiving track. Mistakes are punished harshly.",
    "Miami": "A modern track with a mix of high-speed straights and technical sections.",
    "Monaco": "The crown jewel. Overtaking is nearly impossible, so qualifying is everything.",
    "Baku": "Chaos is the name of the game here with its long straight and tight castle section.",
    "Montréal": "The 'Wall of Champions' awaits. A track that rewards aggressive driving.",
    "Catalunya": "A circuit teams know inside-out. Car performance is truly tested here.",
    "Spielberg": "A short, fast lap with big elevation changes. Expect close racing.",
    "Silverstone": "The historic home of F1. High-speed corners like Maggots and Becketts are legendary.",
    "Budapest": "Often called 'Monaco without the walls'. It's tight, twisty, and hot.",
    "Spa-Francorchamps": "A true driver's circuit. Eau Rouge and Raidillon are iconic.",
    "Zandvoort": "A banked, flowing circuit that is a huge challenge for drivers.",
    "Monza": "The 'Temple of Speed'. It's all about low drag and high straight-line speed.",
    "Singapore": "A grueling, humid night race on a bumpy street circuit.",
    "Suzuka": "A legendary figure-eight track loved by all drivers.",
    "Austin": "A modern classic with a bit of everything, from fast sweeps to heavy braking.",
    "Mexico City": "The high altitude saps engine power and tests cooling systems to their limit.",
    "São Paulo": "Famous for its unpredictable weather and passionate fans. Always exciting.",
    "Las Vegas": "A spectacular night race down the famous Strip. It's all about the show.",
    "Lusail": "A fast, flowing track originally built for MotoGP, making it tough on drivers' necks.",
    "Abu Dhabi": "The season finale. A modern circuit that often hosts title deciders under the lights.",
}

def get_next_gp(gp_name_query=None):
    """Finds the next upcoming F1 Grand Prix."""
    try:
        schedule = fastf1.get_event_schedule(datetime.datetime.now().year, include_testing=False)
        
        # Ensure EventDate is timezone-aware (UTC)
        schedule.loc[:, 'EventDate'] = pd.to_datetime(schedule['EventDate'], utc=True)
        # --- THE ROBUST FIX: Use the most compatible Pandas timestamp generation ---
        now = pd.to_datetime('now', utc=True)
        
        future_events = schedule[schedule['EventDate'] >= now]

        if future_events.empty:
            return None, "No upcoming races found for the rest of the season."

        if gp_name_query:
            event = schedule.get_event_by_name(gp_name_query)
            if event is not None and event['EventDate'] >= now:
                return event, None
            else:
                return None, f"Could not find a future Grand Prix matching '{gp_name_query}'."
        
        return future_events.iloc[0], None
    except Exception as e:
        return None, f"Network error getting race schedule: {e}"

def get_driver_standings():
    """Fetches current driver standings using the fastf1 library by looking at the last race."""
    try:
        year = datetime.datetime.now().year
        schedule = fastf1.get_event_schedule(year, include_testing=False)
        
        # Ensure EventDate is timezone-aware (UTC)
        schedule.loc[:, 'EventDate'] = pd.to_datetime(schedule['EventDate'], utc=True)
        # --- THE ROBUST FIX: Apply the same fix here for consistency ---
        now = pd.to_datetime('now', utc=True)
        
        completed_races = schedule[
            (schedule['EventName'].str.contains("Grand Prix")) & 
            (schedule['EventDate'] < now)
        ]

        if completed_races.empty:
            return None, "The season has not started yet. No standings available."
        
        last_race = completed_races.iloc[-1]
        
        session = fastf1.get_session(year, last_race['RoundNumber'], 'R')
        session.load(telemetry=False, weather=False, messages=False)

        return session.results, None

    except Exception as e:
        return None, f"Could not fetch driver standings using fastf1: {e}"

def generate_prediction(standings_df, event_info):
    """
    Generates a 'prediction' based on current standings and a bit of randomness.
    Accepts a DataFrame from fastf1's session.results.
    """
    if standings_df is None or standings_df.empty:
        return {
            "error": "Cannot generate prediction without driver standings."
        }

    drivers = []
    for index, driver in standings_df.iterrows():
        if pd.isna(driver['Position']):
            continue
        # Robustly get driver name
        if 'GivenName' in driver and 'FamilyName' in driver:
            name = f"{driver['GivenName']} {driver['FamilyName']}"
        elif 'Driver' in driver:
            name = driver['Driver']
        else:
            name = str(driver.get('Abbreviation', 'Unknown'))
        drivers.append({
            "name": name,
            "position": int(driver['Position']),
            "constructor": driver['TeamName']
        })

   # Create a pool of the top 5 contenders
    top_contenders = [d for d in drivers if d['position'] <= 5]
    
    # Make sure we don't try to sample more drivers than we have
    num_to_sample = min(3, len(top_contenders))
    
    # Randomly select 3 unique drivers from the top 5 contenders
    podium_favorites = random.sample(top_contenders, k=num_to_sample)
    midfield_strong = [d for d in drivers if 4 <= d['position'] <= 8]
    dark_horse = random.choice(midfield_strong) if midfield_strong else None
    midfield_pack = [d for d in drivers if 9 <= d['position'] <= 15]
    potential_surprise = random.choice(midfield_pack) if midfield_pack else None
    
    tidbit = "A circuit that always brings excitement!"
    event_name = None
    event_location = None
    if event_info is not None:
        # Try to get EventName and Location as key or attribute
        if isinstance(event_info, dict):
            event_name = event_info.get('EventName')
            event_location = event_info.get('Location')
        else:
            event_name = getattr(event_info, 'EventName', None)
            event_location = getattr(event_info, 'Location', None)
        if event_name:
            for key in CIRCUIT_TIDBITS:
                if key.lower() in event_name.lower():
                    tidbit = CIRCUIT_TIDBITS[key]
                    break

    prediction = {
        "event_name": event_name if event_name else "Unknown Event",
        "location": event_location if event_location else "Unknown Location",
        "tidbit": tidbit,
        "podium_favorites": podium_favorites,
        "dark_horse": dark_horse,
        "potential_surprise": potential_surprise
    }
    
    return prediction