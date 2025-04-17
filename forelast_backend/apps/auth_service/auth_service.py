from supabase import create_client
from django.conf import settings
from supabase.lib import SupabaseException


# Note: Create the tables first at Supabase.
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def register_user(email, password, first_name, last_name, institution):
    result = supabase.auth.sign_up(email = email, password = password)

    if result.user:
        user_id = result.user['id']

        profile_data = {
            "id": user_id,
            "email":  email,
            "first name": first_name,
            "last name": last_name,
            "institution": institution
        }

        supabase.table("user").insert(profile_data).execute()

        return {
            "success": True,
            "user_id": user_id
        }
    else: 
        return {
            "success": False,
            "error": result.get("error", "Registration failed")
        }