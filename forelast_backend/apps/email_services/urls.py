from django.urls import path
from .views import send_suggestion, forgot_password, verify_otp, reset_password, submit_feedback

urlpatterns = [
    path('send-suggestion/', send_suggestion, name='send_suggestion'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('reset-password/', reset_password, name='reset_password'),
    path('submit-feedback/', submit_feedback, name='submit_feedback'),
]
