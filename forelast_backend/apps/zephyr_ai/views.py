from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import zephyr_data, process_message
import os
import requests
import re
from datetime import datetime, timedelta
from supabase import create_client
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def validate_response(text):
    blocked_terms = ["competitor", "politics", "hate speech", "NSFW", "profanity"]
    if any(term in text.lower() for term in blocked_terms):
        return "I can't discuss that topic."
    return text

@api_view(['POST'])
def chat_view(request):
    user_message = request.data.get("message")
    chat_history = request.data.get("history", [])

    if not user_message:
        return Response({"error": "No message provided"}, status=400)

    # Check for weather-related queries
    weather_response = handle_weather_query(user_message)
    if weather_response and isinstance(weather_response, dict):
        return Response({
            "response": weather_response.get('text', ''),
            "source": "weather_api",
            "weather_data": True,
            "structured_data": weather_response.get('data', {}) 
        })

    # Normal chat processing
    local_response = process_message(user_message)
    safe_local_response = validate_response(local_response)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = build_system_prompt(safe_local_response)
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            *chat_history,
            {"role": "user", "content": user_message}
        ],
        "temperature": 1.2,
        "max_tokens": 150
    }

    try:
        res = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers)
        res.raise_for_status()
        deepseek_reply = res.json()["choices"][0]["message"]["content"]
        safe_deepseek_reply = validate_response(deepseek_reply)

        return Response({
            "response": safe_deepseek_reply,
            "source": "deepseek+dictionary" if safe_local_response != zephyr_data["response_logic"]["fallback_response"] else "deepseek"
        })

    except requests.RequestException as e:
        return Response({
            "response": safe_local_response,
            "source": "dictionary (DeepSeek failed)"
        }, status=200)

def build_system_prompt(local_response):
    prompt = (
        "You are Zephyr AI, an AI chatbot for FORELAST. Follow these rules strictly:\n"
        "1. Scope: Only answer questions about FORELAST features, weather data, and policies.\n"
        "2. For weather queries, direct users to ask about specific cities in NCR.\n"
        "3. Tone: Be professional and friendly. Avoid sarcasm or jokes.\n"
        "4. Safety: Never discuss politics, NSFW content, or competitors.\n"
        "5. Format: Keep responses under 3 sentences.\n"
    )
    if local_response != zephyr_data["response_logic"]["fallback_response"]:
        prompt += f"\nHere is some structured knowledge that may help you answer:\n\"{local_response}\"\n"
    return prompt

def handle_weather_query(user_message):
    weather_keywords = ['weather', 'temperature', 'forecast', 'humidity', 'rain', 'precipitation']
    if not any(keyword in user_message.lower() for keyword in weather_keywords):
        return None
    
    cities = [
        'Caloocan', 'Las Piñas', 'Makati', 'Malabon', 'Mandaluyong',
        'Manila', 'Marikina', 'Muntinlupa', 'Navotas', 'Parañaque',
        'Pasay', 'Pasig', 'Pateros', 'Quezon City', 'San Juan',
        'Taguig', 'Valenzuela'
    ]
    
    city = extract_city_from_message(user_message, cities)
    if not city:
        return {
            'text': "I can provide weather information for cities in Metro Manila. Available cities: " + ", ".join(cities),
            'data': {'available_cities': cities}
        }
    
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        normalized_city = normalize_city_name(city)
        
        # Default to current weather unless specifically asking for analytics
        if 'analytics' in user_message.lower() or 'statistics' in user_message.lower():
            return get_analytics_data(supabase, normalized_city, city)
        else:
            return get_current_weather(supabase, normalized_city, city)
            
    except Exception as e:
        logger.error(f"Weather API error for {city}: {str(e)}")
        return {
            'text': f"Sorry, I couldn't fetch weather data for {city}. Please try again later.",
            'data': {'city': city, 'error': str(e)}
        }

def extract_city_from_message(message, cities):
    # Create a mapping of normalized city names to their original forms
    city_mapping = {city.lower().replace('ñ', 'n'): city for city in cities}
    
    # Normalize the message for comparison
    normalized_message = message.lower().replace('ñ', 'n')
    
    # Check for each possible city (normalized version)
    for normalized_city, original_city in city_mapping.items():
        if normalized_city in normalized_message:
            return original_city
    
    # Try more flexible matching if direct match fails
    for city in cities:
        # Match city names with spaces replaced (e.g., "las pinas")
        if city.lower().replace(' ', '').replace('ñ', 'n') in normalized_message.replace(' ', ''):
            return city
        # Match common abbreviations (e.g., "qc" for "quezon city")
        if city.lower() == "quezon city" and " qc " in f" {normalized_message} ":
            return city
    
    return None

def get_current_weather(supabase, normalized_city, city_name):
    forecast_table = f"{normalized_city}_city_forecast"
    today = datetime.now().date().strftime('%Y-%m-%d')
    
    response = supabase.table(forecast_table)\
        .select("*")\
        .eq('datetime', today)\
        .order('datetime', desc=True)\
        .limit(1)\
        .execute()
    
    if not response.data:
        return {
            'text': f"No weather data available for {city_name} today",
            'data': {'city': city_name, 'error': 'No data'}
        }
        
    current_data = response.data[0]
    
    weather_data = {
        'city': city_name,
        'temperature': f"{current_data.get('temp', '--')}°C",
        'condition': get_weather_condition(current_data),
        'humidity': f"{current_data.get('humidity', '--')}%",
        'precipitation': f"{current_data.get('precip', '0')}mm",
        'windspeed': f"{current_data.get('windspeed', '--')} km/h",
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    return {
        'text': f"Current weather for {city_name}",
        'data': weather_data
    }

def get_analytics_data(supabase, normalized_city, city_name):
    weather_table = f"{normalized_city}_city_weather"
    forecast_table = f"{normalized_city}_city_forecast"
    
    # Historical data (14 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)
    historical = supabase.table(weather_table)\
        .select("*")\
        .gte('datetime', start_date.isoformat())\
        .lte('datetime', end_date.isoformat())\
        .execute()
    
    # Forecast data (7 days)
    forecast = supabase.table(forecast_table)\
        .select("*")\
        .gte('datetime', datetime.now().isoformat())\
        .order('datetime')\
        .limit(8)\
        .execute()
        
    return {
        'text': f"Weather data overview for {city_name}",
        'data': {
            'city': city_name,
            'historical_days': len(historical.data) if historical.data else 0,
            'forecast_days': len(forecast.data) if forecast.data else 0
        }
    }

def normalize_city_name(city):
    city = city.lower().strip().replace(' ', '_').replace('ñ', 'n')
    special_cases = {
        "las_piñas": "las_pinas",
        "marikina": "markina",
        "parañaque": "paranaque",
        "quezon_city": "quezon"
    }
    return special_cases.get(city, city)

def get_weather_condition(data):
    temp = data.get('temp', 0)
    precip = data.get('precip', 0)
    
    if not isinstance(temp, (int, float)) or not isinstance(precip, (int, float)):
        return '--'
    
    if (temp >= 26 or temp <= 20) and precip > 50:
        return 'Rainy'
    elif temp > 27:
        return 'Sunny'
    elif temp > 23:
        return 'Partly Cloudy'
    return 'Cloudy'