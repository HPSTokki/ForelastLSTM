from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

User = get_user_model()


@csrf_exempt  
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({ 'detail': 'Invalid JSON format' }, status=400)

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({ 'detail': 'Email and password are required' }, status=400)

        # Check if email exists
        if not User.objects.filter(username=email).exists():
            return JsonResponse({ 'detail': 'Email not found' }, status=404)

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            return JsonResponse({ 'message': 'Login successful' }, status=200)
        else:
            return JsonResponse({ 'detail': 'Incorrect password' }, status=401)
    return JsonResponse({ 'detail': 'Method not allowed' }, status=405)
# Register
@csrf_exempt
def register_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({ 'detail': 'Email and password are required' }, status=400)

        if User.objects.filter(username=email).exists():
            return JsonResponse({ 'detail': 'User already exists' }, status=400)

        User.objects.create_user(username=email, email=email, password=password)

        return JsonResponse({ 'message': 'User registered successfully' }, status=201)

    return JsonResponse({ 'detail': 'Method not allowed' }, status=405)
