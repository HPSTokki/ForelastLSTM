from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail, EmailMessage, get_connection
from django.core.cache import cache
from django.contrib.auth.models import User
import random
import os
import traceback

@csrf_exempt
def send_suggestion(request):
    if request.method == 'POST':
        try:
            message = request.POST.get('message', '')
            print("DEBUG: message =", message)

            if not message:
                return JsonResponse({ 'status': 'error', 'message': 'Message cannot be empty.' }, status=400)

            subject = "New Suggestion from User"
            full_message = f"Suggestion received:\n\n{message}"
            from_email = os.getenv('EMAIL_HOST_USER')

            send_mail(
                subject,
                full_message,
                from_email,
                ['forelastlstm@gmail.com'],
                fail_silently=False,
            )

            return JsonResponse({ 'status': 'success' })

        except Exception as e:
            # Log the full stack trace
            print("ERROR:", str(e))
            print("Traceback:", traceback.format_exc())  # This will print the full traceback to the terminal
            return JsonResponse({ 'status': 'error', 'message': str(e) }, status=500)

    return JsonResponse({ 'status': 'error', 'message': 'Invalid request method' }, status=400)

@csrf_exempt
def submit_feedback(request):
    if request.method == 'POST':
        try:
            feedback = ""

            for key in request.POST:
                if key.startswith("question"):
                    answer_key = key.replace("question", "answer")
                    question = request.POST.get(key)
                    answer = request.POST.get(answer_key, "No answer")
                    feedback += f"Question:\n{question}\nAnswer:\n{answer}\n\n"

            if not feedback:
                return JsonResponse({ 'status': 'error', 'message': 'No feedback submitted.' }, status=400)

            bug_report = request.POST.get('bugReport', '').strip()
            if bug_report:
                feedback += f"Bug Report:\n{bug_report}"

            subject = "New User Feedback"
            from_email = os.getenv('EMAIL_HOST_USER')

            send_mail(
                subject,
                feedback,
                from_email,
                ['forelastlstm@gmail.com'],
                fail_silently=False,
            )

            return JsonResponse({ 'status': 'success' })

        except Exception as e:
            print("ERROR:", str(e))
            print("Traceback:", traceback.format_exc())
            return JsonResponse({ 'status': 'error', 'message': str(e) }, status=500)

    return JsonResponse({ 'status': 'error', 'message': 'Invalid request method' }, status=400)


@csrf_exempt
def forgot_password(request):
    if request.method == 'POST':
        try:
            email = request.POST.get('email', '').strip()
            print("DEBUG: email =", email)

            if not email:
                return JsonResponse({ 'status': 'error', 'message': 'Email is required.' }, status=400)

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Don't reveal whether the email exists
                return JsonResponse({ 'status': 'success', 'message': 'If this email exists, an OTP will be sent.' }, status=200)

            otp = str(random.randint(100000, 999999))
            cache.set(f'otp_{email}', otp, timeout=300)  # Valid for 5 minutes

            subject = 'Your OTP Code'
            message = f'Your OTP code is: {otp}'
            from_email = os.getenv('EMAIL_OTP')

            # Setting up the email connection using the app password
            connection = get_connection(
                host='smtp.gmail.com',
                port=587,
                username=from_email,
                password=os.getenv('EMAIL_OTP_PASSWORD'),  # The app password here
                use_tls=True
            )

            email_message = EmailMessage(
                subject,
                message,
                from_email,
                [email],
                connection=connection
            )
            email_message.send(fail_silently=False)

            return JsonResponse({ 'status': 'success', 'message': 'OTP sent to your email.' })

        except Exception as e:
            print("ERROR:", str(e))
            print("Traceback:", traceback.format_exc())
            return JsonResponse({ 'status': 'error', 'message': str(e) }, status=500)

    return JsonResponse({ 'status': 'error', 'message': 'Invalid request method' }, status=400)

@csrf_exempt
def verify_otp(request):
    if request.method == 'POST':
        try:
            email = request.POST.get('email', '').strip()
            otp_input = request.POST.get('otp', '').strip()

            if not email or not otp_input:
                return JsonResponse({ 'status': 'error', 'message': 'Email and OTP are required.' }, status=400)

            cached_otp = cache.get(f'otp_{email}')
            print(f"DEBUG: cached_otp = {cached_otp}")

            if cached_otp != otp_input:
                return JsonResponse({ 'status': 'error', 'message': 'Invalid or expired OTP.' }, status=400)

            # Optionally, clear OTP after successful verification
            cache.delete(f'otp_{email}')

            return JsonResponse({ 'status': 'success', 'message': 'OTP verified successfully.' })

        except Exception as e:
            print("ERROR:", str(e))
            print("Traceback:", traceback.format_exc())
            return JsonResponse({ 'status': 'error', 'message': str(e) }, status=500)

    return JsonResponse({ 'status': 'error', 'message': 'Invalid request method' }, status=400)

@csrf_exempt
def reset_password(request):
    if request.method == 'POST':
        try:
            email = request.POST.get('email', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()

            if not email or not new_password or not confirm_password:
                return JsonResponse({ 'status': 'error', 'message': 'All fields are required.' }, status=400)

            if new_password != confirm_password:
                return JsonResponse({ 'status': 'error', 'message': 'Passwords do not match.' }, status=400)

            if len(new_password) < 8:
                return JsonResponse({ 'status': 'error', 'message': 'Password must be at least 8 characters.' }, status=400)

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Don't reveal whether user exists
                return JsonResponse({ 'status': 'success', 'message': 'Password reset process completed.' })

            user.set_password(new_password)
            user.save()

            return JsonResponse({ 'status': 'success', 'message': 'Password has been reset successfully.' })

        except Exception as e:
            print("ERROR:", str(e))
            print("Traceback:", traceback.format_exc())
            return JsonResponse({ 'status': 'error', 'message': str(e) }, status=500)

    return JsonResponse({ 'status': 'error', 'message': 'Invalid request method' }, status=400)
