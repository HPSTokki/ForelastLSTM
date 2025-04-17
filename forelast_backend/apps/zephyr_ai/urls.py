from django.urls import path
from forelast_backend.apps.zephyr_ai import views

urlpatterns = [
    path('chat/', views.chat_view, name='chat_view'),
]