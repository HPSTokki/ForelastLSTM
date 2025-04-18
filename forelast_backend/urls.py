"""
URL configuration for forelast_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import WeatherAnalyticsAPI, CurrentWeatherAPI

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/zephyr/', include('forelast_backend.apps.zephyr_ai.urls')),
    path('api/weather/analytics/<str:city>/', WeatherAnalyticsAPI.as_view(), name='weather-analytics'),
    path('api/internal/', include([
        path('current/<str:city>/', CurrentWeatherAPI.as_view()),])),
    path('api/', include('forelast_backend.apps.auth_service.urls')),
]
