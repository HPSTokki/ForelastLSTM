import csv
import requests
import os
from datetime import datetime, date, timedelta

# dont abuse my API key lol


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

# this one is fetching

def fetch_daily_weather(city):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}%20City/{date_yesterday}/{today}?unitGroup=metric&include=days&key={API_KEY}"
    params = {
        'unitGroup': 'metric',
        'key' : API_KEY,
        'contentType': 'json',
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        weather_list = []
        
        if 'days' in data and len(data['days']) > 0:
            for day in data['days']:
                full_data = {
                    'name' : day.get('name', ''),
                    'datetime' : day.get('datetime', ''),
                    'tempmax' : day.get('tempmax', ''),
                    'tempmin' : day.get('tempmin', ''),
                    'temp' : day.get('temp', ''),
                    'feelslikemax' : day.get('feelslikemax', ''),
                    'feelslikemin' : day.get('feelslikemin', ''),
                    'feelslike' : day.get('feelslike', ''),
                    'dew' : day.get('dew', ''),
                    'humidity' : day.get('humidity', ''),
                    'precip' : day.get('precip', ''),
                    'precipprob' : day.get('precipprob', ''),
                    'precipcover' : day.get('precipcover', ''),
                    'preciptype' : day.get('preciptype', ''),
                    'snow' : day.get('snow', ''),
                    'snowdepth' : day.get('snowdepth', ''),
                    'windgust' : day.get('windgust', ''),
                    'windspeed' : day.get('windspeed', ''),
                    'winddir' : day.get('winddir', ''),
                    'sealevelpressure' : day.get('sealevelpressure', ''),
                    'cloudcover' : day.get('cloudcover', ''),
                    'visibility' : day.get('visibility', ''),
                    'solarradiation' : day.get('solarradiation', ''),
                    'solarenergy' : day.get('solarenergy', ''),
                    'uvindex' : day.get('uvindex', ''),
                    'severerisk' : day.get('severerisk', ''),
                    'sunrise' : day.get('sunrise', ''),
                    'sunset' : day.get('sunset', ''),
                    'moonphase' : day.get('moonphase', ''),
                    'conditions' : day.get('conditions', ''),
                    'description' : day.get('description', ''),
                    'icon' : day.get('icon', ''),
                    'stations' : day.get('stations', '')
                }
                filtered_data = {
                    'name': full_data['name'],
                    'datetime': full_data['datetime'],
                    'tempmax': full_data['tempmax'],
                    'tempmin': full_data['tempmin'],
                    'temp': full_data['temp'],
                    'humidity': full_data['humidity'],
                    'precip': full_data['precip'],
                    'windspeed': full_data['windspeed']
                }
                weather_list.append({
                    'full_data': full_data,
                    'filtered_data': filtered_data
                })
            return weather_list
        else: print(f"Error fetching weather data for {city}: {response.status_code}")
    else: print(f"Error fetching weather data for {city}: {response.status_code}")
    
    return None

# idk this is like the one that appends lmao

def append_to_csv(city, full_city_name, weather_list):
    
    filename = f"./WeatherData/{city} City Weather Data.csv"
    
    existing_data = update_csv_if_data_exists(filename)
    
    existing_cities = {(row['name'], row['datetime']): row for row in existing_data}
    
    updated_data = []
    
    for row in weather_list:
        
        row['name'] = full_city_name
        row = row['filtered_data']
        
        if (row['name'], row['datetime']) in existing_cities:
            existing_cities[(row['name'],row['datetime'])] = row
        else:
            updated_data.append(row)
    
    final_data = list(existing_cities.values()) + updated_data
    
    file_exists = os.path.isfile(filename)
    
    fieldnames = ['name', 'datetime', 'tempmax', 'tempmin', 'temp', 'feelslikemax', 'feelslikemin',
        'feelslike', 'dew', 'humidity', 'precip', 'precipprob', 'precipcover', 'preciptype',
        'snow', 'snowdepth', 'windgust', 'windspeed', 'winddir', 'sealevelpressure',
        'cloudcover', 'visibility', 'solarradiation', 'solarenergy', 'uvindex', 'severerisk',
        'sunrise', 'sunset', 'moonphase', 'conditions', 'description', 'icon', 'stations']
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in final_data:
            writer.writerow(row)

def update_csv_if_data_exists(filename):
    if os.path.isfile(filename):
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return list(reader)
    return []

for city in cities:
    print(f"Fetching weather data for {city}...")
    weather_list = fetch_daily_weather(city)
    if weather_list:
        full_city_name = f"{city} City, National Capital Region, Philippines"
        append_to_csv(city, full_city_name, weather_list)