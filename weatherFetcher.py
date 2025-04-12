import csv
import requests
import os
from datetime import datetime

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

def fetch_daily_weather(city):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}%20City/2025-04-12/2025-04-12?unitGroup=metric&include=days&key={API_KEY}"
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
                weather_list.append({
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
                })
            return weather_list
        else: print(f"Error fetching weather data for {city}: {response.status_code}")
    else: print(f"Error fetching weather data for {city}: {response.status_code}")
    
    return None

def append_to_csv(city, weather_list):
    if not weather_list:
        return
    
    for row in weather_list:
        row['name'] = city

    
    filename = f"./WeatherData/{city} City Weather Data.csv"
    file_exists = os.path.isfile(filename)
    
    fieldnames = ['name', 'datetime', 'tempmax', 'tempmin', 'temp', 'feelslikemax', 'feelslikemin',
        'feelslike', 'dew', 'humidity', 'precip', 'precipprob', 'precipcover', 'preciptype',
        'snow', 'snowdepth', 'windgust', 'windspeed', 'winddir', 'sealevelpressure',
        'cloudcover', 'visibility', 'solarradiation', 'solarenergy', 'uvindex', 'severerisk',
        'sunrise', 'sunset', 'moonphase', 'conditions', 'description', 'icon', 'stations']
    
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in weather_list:
            writer.writerow(row)

for city in cities:
    print(f"Fetching weather data for {city}...")
    weather_list = fetch_daily_weather(city)
    append_to_csv(f"{city} City, National Capital Region, Philippines", weather_list);