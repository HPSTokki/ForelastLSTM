import csv
import requests
import os
from datetime import datetime, date, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configuration
today = date.today()
date_yesterday = today - timedelta(days=7)
API_KEY = "YXNCE77CXCVXRPX63EW7652JS"

# Supabase configuration
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

cities = ['Caloocan', 'Las Piñas', 'Makati', 'Malabon', 'Mandaluyong', 
          'Manila', 'Marikina', 'Muntinlupa', 'Navotas', 'Parañaque',
          'Pasay', 'Pasig','Pateros', 'Quezon', 'San Juan', 'Taguig', 'Valenzuela']

CSV_COLUMNS = ['name', 'datetime', 'tempmax', 'tempmin', 'temp', 
               'humidity', 'precip', 'windspeed']

def fetch_daily_weather(city):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}%20City/{date_yesterday}/{today}?unitGroup=metric&include=days&key={API_KEY}"
    response = requests.get(url, params={
        'unitGroup': 'metric',
        'key': API_KEY,
        'contentType': 'json'
    })
    
    if response.status_code != 200:
        print(f"Error fetching {city}: HTTP {response.status_code}")
        return None
        
    data = response.json()
    if not data.get('days'):
        print(f"No weather data found for {city}")
        return None
        
    weather_list = []
    for day in data['days']:
        weather_list.append({
            'name': f"{city} City, National Capital Region, Philippines",
            'datetime': day['datetime'],  # Keep as string for CSV
            'tempmax': float(day.get('tempmax', 0)),
            'tempmin': float(day.get('tempmin', 0)),
            'temp': float(day.get('temp', 0)),
            'humidity': float(day.get('humidity', 0)),
            'precip': float(day.get('precip', 0)),
            'windspeed': float(day.get('windspeed', 0))
            # date_added is handled by Supabase default
        })
    return weather_list

def get_table_name(city):
    """Helper function to ensure consistent table naming"""
    city = city.lower().replace(' ', '_').replace('ñ', 'n')
    # Special case corrections
    if city == "las_piñas": city = "las_pinas"
    if city == "marikina": city = "markina"  # Your table uses 'markina'
    if city == "parañaque": city = "paramaque"
    return f"{city}_city_weather"

def save_to_supabase(city, weather_data):
    table_name = get_table_name(city)  # Use the consistent naming
    
    try:
        # Convert data types to match your table schema
        supabase_data = []
        for entry in weather_data:
            supabase_entry = {
                'datetime': str(entry['datetime']),  # Ensure string type
                'name': str(entry['name']),
                'tempmax': float(entry['tempmax']) if entry['tempmax'] is not None else None,
                'tempmin': float(entry['tempmin']) if entry['tempmin'] is not None else None,
                'temp': float(entry['temp']) if entry['temp'] is not None else None,
                'humidity': float(entry['humidity']) if entry['humidity'] is not None else None,
                'precip': float(entry['precip']) if entry['precip'] is not None else None,
                'windspeed': float(entry['windspeed']) if entry['windspeed'] is not None else None
            }
            supabase_data.append(supabase_entry)
        
        response = supabase.table(table_name).upsert(supabase_data, on_conflict='datetime').execute()
        
        if response.data and len(response.data) == len(weather_data):
            print(f"✓ {city}: Successfully saved {len(response.data)} records")
            return True
        print(f"⚠ {city}: Save operation completed but data count mismatch")
        return False
    except Exception as e:
        print(f"✗ {city} Supabase error details:")
        print(f"- Error type: {type(e).__name__}")
        print(f"- Full error: {str(e)}")
        if weather_data:
            print("- First record that failed:", supabase_data[0] if supabase_data else weather_data[0])
        return False

def append_to_csv(city, weather_list):
    filename = f"./WeatherData/{city} City Weather Data.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    existing_entries = set()
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_entries = {(row['name'], row['datetime']) for row in reader}
    
    new_entries = [
        {k: v for k, v in entry.items() if k in CSV_COLUMNS}
        for entry in weather_list
        if (entry['name'], entry['datetime']) not in existing_entries
    ]
    
    if new_entries:
        write_header = not os.path.exists(filename)
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerows(new_entries)
        print(f"✓ {city}: Added {len(new_entries)} to CSV")
    else:
        print(f"○ {city}: No new CSV entries")
    
    return new_entries

def verify_tables():
    missing_tables = []
    for city in cities:
        table_name = get_table_name(city)
        try:
            response = supabase.table(table_name).select("datetime", count='exact').limit(1).execute()
            if not isinstance(response.data, list):
                missing_tables.append(table_name)
        except Exception as e:
            print(f"Table check failed for {table_name}: {str(e)}")
            missing_tables.append(table_name)
    
    if missing_tables:
        print("\nMISSING TABLES IN SUPABASE:")
        print("These tables are missing or inaccessible:")
        for table in missing_tables:
            print(f"- {table}")
        return False
    return True

def main():
    if not verify_tables():
        print("Please create the missing tables first")
        return
    
    for city in cities:
        print(f"\n{'='*30}\nProcessing {city}...")
        weather_data = fetch_daily_weather(city)
        if not weather_data:
            continue
            
        new_entries = append_to_csv(city, weather_data)
        if new_entries:
            save_to_supabase(city, new_entries)

if __name__ == "__main__":
    main()