from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import zephyr_data, process_message  # NLP knowledge base
import os
import requests

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
        "1. Scope: Only answer questions about FORELAST features and policies.\n"
        "2. Tone: Be professional and friendly. Avoid sarcasm or jokes.\n"
        "3. Safety: Never discuss politics, NSFW content, or competitors.\n"
        "4. Format: Keep responses under 3 sentences.\n"
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
