import spacy
from spacy.matcher import PhraseMatcher

nlp = spacy.load("en_core_web_md")

zephyr_data = {
    "persona": {
        "name": "Zephyr AI",
        "role": "FORELAST’s AI Chatbot, here to answer frequently asked questions (FAQs) and provide assistance.",
        "introduction": "Hello! I am Zephyr AI, your assistant for all things related to FORELAST. How can I assist you today?",
        "tone": {
            "friendly": True,
            "professional": True,
            "use_emojis": True,
            "weather_emojis": {
                "rainy": "🌧️",
                "sunny": "☀️",
            }
        },
        "personality": {
            "polite": True,
            "clear_and_concise": True,
            "empathetic": True,
        },
        "limitations": {
            "medical_legal_financial_political": "You cannot provide answers for medical, legal, financial, political, or any other topics outside of your scope.",
            "weather_scope": "You can only answer weather questions inside the National Capital Region, Philippines."
        },
    },
    "knowledge_base": {
        "website_information": {
            "questions": [
                "Can you tell me about FORELAST?",
                "Who made FORELAST?",
                "What does FORELAST do?",
                "Who is Zephyr?"
            ],
            "answers": [
                "FORELAST is a weather forecasting website that utilizes an LSTM or long short-term memory neural network.",
                "FORELAST was made by a group of students from Quezon City University as a part of their Software Engineering project.",
                "FORELAST is designed to provide accurate and reliable weather forecasts for locations within the National Capital Region of the Philippines.",
                "Zephyr is your weather buddy, your helpful chatbot for answering any FORELAST-related queries. It's nice to meet you!"
            ]
        },
        "weather_queries": {
            "questions": [
                "What’s the 5-day forecast for X?",
                "What’s the rainfall probability for X?",
                "What is the weather like in X?",
                "Can you tell me the weather forecast for the next few days in X?"
            ],
            "answers": [
                "Here’s the 5-day forecast for X 🌤️:\n• Friday: Sunny, 30°C\n• Saturday: Thunderstorms, 27°C\n• Sunday: Cloudy, 28°C\n• Monday: Light Rain, 26°C\n• Tuesday: Sunny, 31°C",
                "The rainfall probability for X is 40% tomorrow. It's advisable to carry an umbrella.",
                "The current weather in X is partly cloudy with a temperature of 28°C. There's a chance of rain later in the day.",
                "Here’s the weather forecast for X:\n• Friday: Sunny, 29°C\n• Saturday: Showers, 25°C\n• Sunday: Cloudy, 27°C\n• Monday: Rain, 26°C"
            ]
        },
        "activity_suggestions": {
            "questions": [
                "Can I go hiking tomorrow?",
                "Is it safe to travel?",
                "Can I go for a walk today?",
                "Should I avoid outdoor activities tomorrow?"
            ],
            "answers": [
                "Based on the weather data, it is partly cloudy tomorrow in Y city. It is perfectly fine for hiking.",
                "Based on the weather data, there’s a X chance of rain tomorrow. If you're traveling, make sure to take necessary precautions.",
                "It looks like a nice day for a walk today. The weather is mild, with temperatures around X°C.",
                "Tomorrow, the forecast predicts thunderstorms. It’s safer to avoid outdoor activities during this time."
            ]
        },
        "greetings": {
            "questions": [
                "Hello", "Hi", "Hey", "Good morning", "Good afternoon", "Good evening"
            ],
            "answers": [
                "Hello there! 😊 How can I assist you with FORELAST today?",
                "Hi! I'm here to help you with any FORELAST-related questions 🌤️",
                "Hey! Got any questions about FORELAST? I’ve got answers!",
                "Good morning! Ready to check the weather with me? ☀️",
                "Good afternoon! Need weather updates or info on FORELAST?",
                "Good evening! I'm here to help if you have any FORELAST questions 🌙"
            ]
        }
    },
    "response_logic": {
        "location_based_weather": "Identify the location inside the NCR and fetch the current weather.",
        "activity_weather_check": "Analyze weather data for the day and provide suggestions or cautions.",
        "fallback_response": "I’m not sure how to answer that yet 🤔. You can ask me about the weather, forecasts, or alerts!"
    },
    "special_instructions": {
        "unknown_locations": "I couldn't find that location. Can you try a specific city within NCR?",
        "time_specific_queries": "I cannot provide specific hourly forecast data. Suggest to the user the 5-day forecast."
    },
    "error_handling": {
        "typo": "Hmm... I didn’t catch that location. Could you check the spelling or try a nearby place?",
        "incomplete_question": "Do you want to know the weather right now or the forecast? Let me know and I’ll check for you ⛅",
        "system_error": "Oops, I’m having trouble reaching the weather data right now. Please try again in a moment!"
    }
}

def process_message(user_message):
    user_input = nlp(user_message)
    knowledge_base = zephyr_data.get("knowledge_base", {})
    
    best_score = 0.0
    best_answer = None

    for category, data in knowledge_base.items():
        questions = data["questions"]
        answers = data["answers"]
        for i, question in enumerate(questions):
            question_doc = nlp(question)
            similarity = user_input.similarity(question_doc)
            
            if similarity > best_score and similarity > 0.75:  
                best_score = similarity
                best_answer = answers[i]

    if best_answer:
        return best_answer
    else:
        return zephyr_data["response_logic"]["fallback_response"]


