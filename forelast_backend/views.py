from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class WeatherAnalyticsAPI(View):
    def get(self, request, city):
        try:
            supabase = self._get_supabase_client()
            
            # Get normalized table names
            weather_table = self._get_weather_table_name(city)
            forecast_table = self._get_forecast_table_name(city)
            
            # Get historical data (14 days) from weather table
            historical = self._fetch_historical_data(supabase, weather_table)
            
            # Get forecast data (7 days) from forecast table
            forecast = self._fetch_forecast_data(supabase, forecast_table)
            
            # Process and combine data
            response_data = {
                'city': city.title(),
                'historical': self._process_data(historical),
                'forecast': self._process_data(forecast),
                'combined': self._process_data(pd.concat([historical, forecast])),
                'last_updated': datetime.now().isoformat(),
                'tables_used': {
                    'historical': weather_table,
                    'forecast': forecast_table
                }
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"Error processing request for {city}: {str(e)}")
            return JsonResponse(
                {'error': 'Failed to fetch weather data', 'details': str(e)},
                status=500
            )

    def _get_supabase_client(self):
        """Initialize and return Supabase client"""
        return create_client(
            os.getenv('SUPABASE_URL'), 
            os.getenv('SUPABASE_KEY')
        )

    def _get_weather_table_name(self, city):
        """Get table name for historical weather data"""
        base_name = self._normalize_city_name(city)
        return f"{base_name}_city_weather"

    def _get_forecast_table_name(self, city):
        """Get table name for forecast data"""
        base_name = self._normalize_city_name(city)
        return f"{base_name}_city_forecast"

    def _normalize_city_name(self, city):
        """Normalize city name for table lookup"""
        city = city.lower().strip().replace(' ', '_').replace('ñ', 'n')
        
        # Handle all possible Philippine city name variations
        special_cases = {
            "las_piñas": "las_pinas",
            "marikina": "markina",
            "parañaque": "paranaque",
            "caloocan": "caloocan",
            "quezon_city": "quezon",
            "manila": "manila"
        }
        return special_cases.get(city, city)

    def _fetch_historical_data(self, supabase, table_name):
        """Fetch last 14 days of historical data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)
        
        logger.info(f"Fetching historical data from {table_name}")
        
        response = supabase.table(table_name)\
            .select("*")\
            .gte('datetime', start_date.isoformat())\
            .lte('datetime', end_date.isoformat())\
            .order('datetime', desc=False   )\
            .execute()
            
        logger.info(f"Found {len(response.data)} historical records")
        return pd.DataFrame(response.data)

    def _fetch_forecast_data(self, supabase, table_name):
        """Fetch next 7 days of forecast data"""
        logger.info(f"Fetching forecast data from {table_name}")
        
        response = supabase.table(table_name)\
            .select("*")\
            .gte('datetime', datetime.now().isoformat())\
            .order('datetime')\
            .limit(8)\
            .execute()
            
        logger.info(f"Found {len(response.data)} forecast records")
        return pd.DataFrame(response.data)

    def _process_data(self, df):
        """Process DataFrame into API-ready format"""
        if df.empty:
            return {
                'dates': [],
                'temp': [],
                'humidity': [],
                'precip': [],
                'windspeed': []
            }
            
        df['datetime'] = pd.to_datetime(df['datetime'])
        return {
            'dates': df['datetime'].dt.strftime('%b %d').tolist(),
            'temp': df['temp'].round(1).tolist(),
            'humidity': df['humidity'].round(1).tolist(),
            'precip': df['precip'].round(1).tolist(),
            'windspeed': df['windspeed'].round(1).tolist()
        }