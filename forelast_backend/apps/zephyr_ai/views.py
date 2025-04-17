from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import zephyr_data
from .utils import process_message  # Import the process_message function
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
    """
    Handle chat request. It first looks for relevant information in the knowledge base using NLP.
    If not found, it will call the DeepSeek API.
    """
    user_message = request.data.get("message")
    chat_history = request.data.get("history", [])

    if not user_message:
        return Response({"error": "No message provided"}, status=400)

    # Step 1: Use NLP to check if the user query can be answered by the knowledge base
    response = process_message(user_message)

    # If the knowledge base doesn't contain relevant content, use the DeepSeek API
    if response == "Sorry, I couldn't understand your question. Can you please rephrase?":
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Zephyr AI, an AI chatbot for FORELAST. Follow these rules strictly:\n"
                        "1. Scope: Only answer questions about FORELAST features and policies.\n"
                        "2. Tone: Be professional and friendly. Avoid sarcasm or jokes.\n"
                        "3. Safety: Never discuss politics, NSFW content, or competitors.\n"
                        "4. Format: Keep responses under 3 sentences."
                    )
                },
                *chat_history,
                {"role": "user", "content": user_message}
            ],
            "temperature": 1.3,
            "max_tokens": 150
        }

        try:
            res = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers)
            res.raise_for_status()
            bot_reply = res.json()["choices"][0]["message"]["content"]
            safe_reply = validate_response(bot_reply)
            return Response({"response": safe_reply})

        except requests.RequestException as e:
            return Response({"error": str(e)}, status=500)

    else:
        # If the knowledge base contains relevant content, return the response
        return Response({"response": response})
