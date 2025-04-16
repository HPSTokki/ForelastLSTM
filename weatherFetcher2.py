import csv
import requests
import os
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import env

supabaseURL = os.environ['SUPABASE_URL']
supabaseKEY= os.environ['SUPABASE_KEY']
supabase: Client = create_client(supabaseURL, supabaseKEY)

today = date.today()
date_yesterday = today - timedelta(days=1)
API_KEY = "YXNCE77CXCVXRPX63EW7652JS"

cities = ['Caloocan',
          'Las Piñas',
          'Makati',
          'Malabon',
          'Mandaluyong',
          'Manila',
          'Marikina',
          'Muntinlupa',
          'Navotas',
          'Parañaque',
          'Pasay',
          'Pasig',
          'Quezon',
          'San Juan',
          'Taguig',
          'Valenzuela']

# Define the columns we want to keep in the final CSV
CSV_COLUMNS = ['name', 'datetime', 'tempmax', 'tempmin', 'temp', 
               'humidity', 'precip', 'windspeed']

def fetch_daily_weather(city):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}%20City/{date_yesterday}/{today}?unitGroup=metric&include=days&key={API_KEY}"
    params = {
        'unitGroup': 'metric',
        'key': API_KEY,
        'contentType': 'json',
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        weather_list = []
        
        if 'days' in data and len(data['days']) > 0:
            for day in data['days']:
                full_city_name = f"{city} City, National Capital Region, Philippines"
                
                # Create a dictionary with only the columns we want
                weather_data = {
                    'name': full_city_name,
                    'datetime': day.get('datetime', ''),
                    'tempmax': day.get('tempmax', ''),
                    'tempmin': day.get('tempmin', ''),
                    'temp': day.get('temp', ''),
                    'humidity': day.get('humidity', ''),
                    'precip': day.get('precip', ''),
                    'windspeed': day.get('windspeed', ''),
                    'date_added': datetime.now().isoformat()
                }
                weather_list.append(weather_data)
            return weather_list
        else:
            print(f"Error: No days data found for {city}")
    else:
        print(f"Error fetching weather data for {city}: {response.status_code}")
    return None

def save_to_supabase(weather_data):
    try: 
        table_name = f"{city.lower().replace(' ', '_').replace('ñ', 'n')}_city_data"
        
        try:
            supabase.table(table_name).select("*").limit(1).execute()
        except Exception as e:
            create_table_sql = f"""
            CREATE TABLE {table_name} (
                name text,
                string timestamp,  -- Assuming this is the datetime field
                tempmax double precision,
                tempmin double precision,
                temp double precision,
                humidity double precision,
                precip double precision,
                windspeed double precision
            );
            """
            supabase.rpc('execute_sql', {'quert': create_table_sql}).execute()
        response = supabase.table(table_name).upsert(weather_data, on_conflict="datetime").execute()
    
        if hasattr(response, 'error') and response.error:
            print(f'Supabase Error {city}: {response.error}')
            return False
        print(f"Successfuly saved {len(weather_data)} records to {table_name}")
        return True
    except Exception as e:
        print(f"Error saving {city} to Supabase: {str(e)}")
        return False
            

def append_to_csv(city, weather_list):
    filename = f"./WeatherData/{city} City Weather Data.csv"
    
    existing_data = []
    # Read existing data, but only keep the columns we want
    if os.path.isfile(filename):
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Filter the row to only include our desired columns
                filtered_row = {col: row.get(col, '') for col in CSV_COLUMNS}
                existing_data.append(filtered_row)
    
    # Create a set of existing (name, datetime) pairs for quick lookup
    existing_entries = {(row['name'], row['datetime']) for row in existing_data}
    
    # Add new entries that don't already exist
    for new_row in weather_list:
        if (new_row['name'], new_row['datetime']) not in existing_entries:
            existing_data.append(new_row)
    
    # Write all data back to the file
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(existing_data)

for city in cities:
    print(f"Fetching weather data for {city}...")
    weather_list = fetch_daily_weather(city)
    if weather_list:
        append_to_csv(city, weather_list)