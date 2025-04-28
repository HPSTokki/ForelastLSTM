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
from django.http import HttpResponse

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class CurrentWeatherAPI(View):
    """API endpoint for getting current weather data only"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, city):
        try:
            supabase = self._get_supabase_client()
            forecast_table = self._get_forecast_table_name(city)
            today = datetime.now().date().strftime('%Y-%m-%d')
            
            response = supabase.table(forecast_table)\
                .select("*")\
                .eq('datetime', today)\
                .order('datetime', desc=True)\
                .limit(1)\
                .execute()
            
            if not response.data:
                return JsonResponse(
                    {'error': 'No forecast data available'}, 
                    status=404
                )
                
            current_data = response.data[0]

            return JsonResponse({
                'city': city.title(),
                'temperature': current_data.get('temp', '--'),
                'weather_condition': self._get_weather_condition(current_data),
                'humidity': current_data.get('humidity', '--'),
                'precip': current_data.get('precip', 0),
                'windspeed': current_data.get('windspeed', '--'),
                'last_updated': datetime.now().isoformat()
            }, content_type="application/json")
            
        except Exception as e:
            logger.error(f"Error fetching current weather for {city}: {str(e)}")
            return JsonResponse(
                {'error': 'Failed to fetch current weather', 'details': str(e)},
                status=500
            )

    def _get_supabase_client(self):
        """Initialize and return Supabase client"""
        return create_client(
            os.getenv('SUPABASE_URL'), 
            os.getenv('SUPABASE_KEY')
        )

    def _get_forecast_table_name(self, city):
        """Get table name for forecast data"""
        base_name = self._normalize_city_name(city)
        return f"{base_name}_city_forecast"

    def _normalize_city_name(self, city):
        """Normalize city name for table lookup"""
        city = city.lower().strip().replace(' ', '_').replace('ñ', 'n')
        special_cases = {
            "las_piñas": "las_pinas",
            "marikina": "markina",
            "parañaque": "paranaque",
            "caloocan": "caloocan",
            "quezon_city": "quezon",
            "manila": "manila"
        }
        return special_cases.get(city, city)

    def _get_weather_condition(self, data):
        """Determine weather condition based on weather data"""
        temp = data.get('temp', 0)
        precip = data.get('precip', 0)
        
        if (temp >= 26 or temp <= 20) and precip > 50:
            return 'Rainy'
        elif temp > 27:
            return 'Sunny'
        elif temp > 23:
            return 'Partly Cloudy'
        else:
            return 'Cloudy'

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
        
class WeatherDataDownloadAPI(View):
    """API endpoint for downloading weather data as CSV"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, city):
        try:
            # Validate and parse dates
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if not start_date or not end_date:
                return JsonResponse(
                    {'error': 'Both start_date and end_date parameters are required'},
                    status=400
                )
            
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=400
                )
            
            if start_date > end_date:
                return JsonResponse(
                    {'error': 'Start date cannot be after end date'},
                    status=400
                )
            
            supabase = self._get_supabase_client()
            weather_table = self._get_weather_table_name(city)
            
            logger.info(f"Fetching data from {weather_table} between {start_date} and {end_date}")
            
            # Fetch data within date range
            try:
                query_result = supabase.table(weather_table)\
                        .select("*")\
                        .gte('datetime', start_date.isoformat())\
                        .lte('datetime', end_date.isoformat())\
                        .order('datetime')\
                        .execute()
            except Exception as e:
                if "relation" in str(e) and "does not exist" in str(e):
                    return JsonResponse(
                        {'error': f'No data available for {city}'},
                        status=404
                    )
                raise
                
            logger.info(f"Found {len(query_result.data)} records")
            
            if not query_result.data:
                return JsonResponse(
                    {'error': 'No data available for the selected date range'},
                    status=404
                )
                
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{city}_weather_data_{start_date}_to_{end_date}.csv"'
            
            df = pd.DataFrame(query_result.data)
            df.to_csv(response, index=False)
            return response
            
        except Exception as e:
            logger.error(f"Error downloading data for {city}: {str(e)}", exc_info=True)
            return JsonResponse(
                {'error': 'Failed to download data', 'details': str(e)},
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
    
class WeatherDataPreviewAPI(View):
    """API endpoint for previewing weather data"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, city):
        try:
            # Validate and parse dates
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if not start_date or not end_date:
                return JsonResponse(
                    {'error': 'Both start_date and end_date parameters are required'},
                    status=400
                )
            
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=400
                )
            
            if start_date > end_date:
                return JsonResponse(
                    {'error': 'Start date cannot be after end date'},
                    status=400
                )
            
            supabase = self._get_supabase_client()
            weather_table = self._get_weather_table_name(city)
            
            logger.info(f"Fetching preview data from {weather_table} between {start_date} and {end_date}")
            
            # First get total count
            count_response = supabase.table(weather_table)\
                .select("count", count="exact")\
                .gte('datetime', start_date.isoformat())\
                .lte('datetime', end_date.isoformat())\
                .execute()
            
            total_records = count_response.count
            
            # Then get preview data (first 10 records)
            response = supabase.table(weather_table)\
                .select("*")\
                .gte('datetime', start_date.isoformat())\
                .lte('datetime', end_date.isoformat())\
                .order('datetime')\
                .limit(10)\
                .execute()
                
            if not response.data:
                return JsonResponse(
                    {'error': 'No data available for the selected date range'},
                    status=404
                )
                
            return JsonResponse({
                'preview': response.data,
                'total_records': total_records
            })
            
        except Exception as e:
            logger.error(f"Error previewing data for {city}: {str(e)}", exc_info=True)
            return JsonResponse(
                {'error': 'Failed to fetch preview data', 'details': str(e)},
                status=500
            )

    # Include all the same helper methods as in WeatherDataDownloadAPI
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

class TopCitiesAPI(View):
    """API endpoint for getting top cities by temperature"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        try:
            supabase = self._get_supabase_client()
            
            # Get current date
            today = datetime.now().date().isoformat()
            
            # We'll check forecast tables for major cities
            cities = [
                "Manila", "Quezon City", "Caloocan", "Las Piñas", "Makati",
                "Malabon", "Mandaluyong", "Marikina", "Muntinlupa", "Navotas",
                "Parañaque", "Pasay", "Pasig", "San Juan", "Taguig", "Valenzuela"
            ]
            
            top_cities = []
            
            for city in cities:
                table_name = self._get_forecast_table_name(city)
                try:
                    response = supabase.table(table_name)\
                        .select("temp")\
                        .eq('datetime', today)\
                        .limit(1)\
                        .execute()
                    
                    if response.data:
                        top_cities.append({
                            'city': city,
                            'temp': response.data[0].get('temp', 0)
                        })
                except Exception as e:
                    logger.warning(f"Could not fetch data for {city}: {str(e)}")
                    continue
            
            # Sort by temperature (descending) and take top 5
            top_cities_sorted = sorted(top_cities, key=lambda x: x['temp'], reverse=True)[:5]
            
            return JsonResponse({
                'top_cities': top_cities_sorted,
                'last_updated': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error fetching top cities: {str(e)}")
            return JsonResponse(
                {'error': 'Failed to fetch top cities', 'details': str(e)},
                status=500
            )

    def _get_supabase_client(self):
        """Initialize and return Supabase client"""
        return create_client(
            os.getenv('SUPABASE_URL'), 
            os.getenv('SUPABASE_KEY')
        )

    def _get_forecast_table_name(self, city):
        """Get table name for forecast data"""
        base_name = self._normalize_city_name(city)
        return f"{base_name}_city_forecast"

    def _normalize_city_name(self, city):
        """Normalize city name for table lookup"""
        city = city.lower().strip().replace(' ', '_').replace('ñ', 'n')
        special_cases = {
            "las_piñas": "las_pinas",
            "marikina": "markina",
            "parañaque": "paranaque",
            "caloocan": "caloocan",
            "quezon_city": "quezon",
            "manila": "manila"
        }
        return special_cases.get(city, city)