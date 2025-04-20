from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import zephyr_data, process_message
import os
import requests
import re
from datetime import datetime

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

    # Rest of your existing chat_view code...
    # Get local NLP-based response
    local_response = process_message(user_message)
    safe_local_response = validate_response(local_response)

    # Build DeepSeek prompt
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are Zephyr AI, an AI chatbot for FORELAST. Follow these rules strictly:\n"
        "1. Scope: Only answer questions about FORELAST features, weather data, and policies.\n"
        "2. For weather queries, direct users to ask about specific cities in NCR.\n"
        "3. Tone: Be professional and friendly. Avoid sarcasm or jokes.\n"
        "4. Safety: Never discuss politics, NSFW content, or competitors.\n"
        "5. Format: Keep responses under 3 sentences.\n"
        "Available cities: Caloocan, Las Piñas, Makati, Malabon, Mandaluyong, "
        "Manila, Marikina, Muntinlupa, Navotas, Parañaque, Pasay, Pasig, "
        "Pateros, Quezon City, San Juan, Taguig, Valenzuela"
    )

    # If there's a confident local answer, include it in the system message
    if safe_local_response != zephyr_data["response_logic"]["fallback_response"]:
        system_prompt += f"\nHere is some structured knowledge that may help you answer:\n\"{safe_local_response}\"\n"

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
        # fallback to local response if DeepSeek fails
        return Response({
            "response": safe_local_response,
            "source": "dictionary (DeepSeek failed)"
        }, status=200)

def handle_weather_query(user_message):
    """Handle weather-related queries by calling appropriate APIs"""
    weather_keywords = ['weather', 'temperature', 'forecast', 'humidity', 'rain', 'precipitation']
    if not any(keyword in user_message.lower() for keyword in weather_keywords):
        return None
    
    cities = [
        'Caloocan', 'Las Piñas', 'Makati', 'Malabon', 'Mandaluyong',
        'Manila', 'Marikina', 'Muntinlupa', 'Navotas', 'Parañaque',
        'Pasay', 'Pasig', 'Pateros', 'Quezon City', 'San Juan',
        'Taguig', 'Valenzuela'
    ]
    
    city_pattern = r'\b(?:' + '|'.join(cities) + r')\b'
    match = re.search(city_pattern, user_message, re.IGNORECASE)
    
    date_pattern = r'(today|tomorrow|\d{4}-\d{2}-\d{2}|next week)'
    date_match = re.search(date_pattern, user_message, re.IGNORECASE)
    date_context = date_match.group(0) if date_match else None
    
    if not match:
        return {
            'text': (
                "I can provide weather information for cities in Metro Manila. "
                "Available cities: " + ", ".join(cities) + ". "
                "Please specify which city you're interested in."
            ),
            'data': {'available_cities': cities}
        }
    
    city = match.group(0)
    
    try:
        normalized_city = normalize_city_name(city)
        
        if date_context and date_context.lower() in ['today', 'tomorrow']:
            response = requests.get(
                f'http://localhost:8000/api/internal/current/{normalized_city}/',
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                return format_current_weather(city, data, date_context)
        
        response = requests.get(
            f'http://localhost:8000/api/internal/analytics/{normalized_city}/',
            headers={'Accept': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            return format_analytics_response(city, data, date_context)
            
        return {
            'text': f"I couldn't retrieve weather data for {city}. Please try again later.",
            'data': {'city': city, 'error': 'Data unavailable'}
        }
        
    except Exception as e:
        print(f"Error fetching weather data: {str(e)}")
        return {
            'text': f"I encountered an error while fetching weather data for {city}.",
            'data': {'city': city, 'error': str(e)}
        }

def normalize_city_name(city):
    """Normalize city name for API requests"""
    city = city.lower().strip().replace(' ', '_').replace('ñ', 'n')
    special_cases = {
        "las_piñas": "las_pinas",
        "marikina": "markina",
        "parañaque": "paranaque",
        "quezon_city": "quezon"
    }
    return special_cases.get(city, city)

def format_current_weather(city, data, time_context="now"):
    """Format current weather API response"""
    time_text = {
        'today': "Today in",
        'tomorrow': "Tomorrow in",
    }.get(time_context.lower(), "Current weather in")
    
    weather_data = {
        'city': city,
        'temperature': data.get('temperature', '--'),
        'condition': data.get('weather_condition', '--'),
        'humidity': data.get('humidity', '--'),
        'precipitation': data.get('precip', '0'),
        'wind_speed': data.get('windspeed', '--'),
        'last_updated': data.get('last_updated', '--')
    }
    
    return {
        'text': (
            f"{time_text} {city}:\n"
            f"• Temperature: {weather_data['temperature']}°C\n"
            f"• Condition: {weather_data['condition']}\n"
            f"• Humidity: {weather_data['humidity']}%\n"
            f"• Precipitation: {weather_data['precipitation']}mm\n"
            f"• Wind Speed: {weather_data['wind_speed']} km/h\n"
            f"• Last Updated: {weather_data['last_updated']}"
        ),
        'data': weather_data
    }

def format_analytics_response(city, data, time_context=None):
    """Format analytics API response"""
    if not time_context:
        weather_data = {
            'city': city,
            'historical_days': len(data.get('historical', {}).get('dates', [])),
            'forecast_days': len(data.get('forecast', {}).get('dates', []))
        }
        
        return {
            'text': (
                f"Weather data for {city}:\n"
                f"• Historical: {weather_data['historical_days']} days available\n"
                f"• Forecast: {weather_data['forecast_days']} days available\n"
                "For detailed data, please visit the Analytics section."
            ),
            'data': weather_data
        }
    
    return {
        'text': "I can provide detailed weather analytics. Please specify if you want historical or forecast data.",
        'data': {'city': city}
    }