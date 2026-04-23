"""
This file handles all the supabase authentication logic, including 
sign up, sign in, and sign out. It also provides a way to get the current user and check if the user is authenticated.
    

"""

import os
from datetime import date
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL      = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ── Auth ──────────────────────────────────────────────────────────────────────

def exchange_code_for_session(code: str):
    """Exchange OAuth code for session (PKCE flow)."""
    try:
        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        return {"success": True, "user": res.user, "session": res.session}
    except Exception as e:
        return {"success": False, "error": str(e)}



def sign_up(email: str, password: str):
    """Create a new account with email and password."""
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return {"success": True, "user": res.user}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_in(email: str, password: str):
    """Sign in with email and password."""
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return {"success": True, "user": res.user, "session": res.session}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_in_with_google():
    """Get the Google OAuth redirect URL using PKCE flow."""
    try:
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "https://interviewcoach-ai.streamlit.app",
                "query_params": {
                    "access_type": "offline",
                    "prompt": "consent",
                },
                "flow_type": "pkce"
            }
        })
        return {"success": True, "url": res.url}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_out():
    """Sign out the current user."""
    try:
        supabase.auth.sign_out()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def set_supabase_session(access_token: str, refresh_token: str):
    """Set the session so RLS policies work correctly."""
    try:
        supabase.auth.set_session(access_token, refresh_token)
    except Exception as e:
        print(f"set_session error: {e}")

# ── Profile ───────────────────────────────────────────────────────────────────

def get_profile(user_id: str):
    try:
        res = supabase.table("profiles") \
            .select("*") \
            .eq("id", user_id) \
            .execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        print(f"get_profile error: {e}")
        return None


def is_paid_user(user_id: str) -> bool:
    """Check if the user is on the paid tier."""
    profile = get_profile(user_id)
    if not profile:
        return False
    return profile.get("tier") == "paid"


# ── Usage tracking ────────────────────────────────────────────────────────────

MAX_FREE_ANALYSES = 3

def check_and_increment_usage(user_id: str) -> dict:
    """
    Check if a free user can run an analysis.
    If yes, increment their count and return allowed=True.
    If no, return allowed=False with remaining count.
    Returns: { allowed: bool, analyses_today: int, remaining: int }
    """
    profile = get_profile(user_id)
    if not profile:
        return {"allowed": False, "error": "Profile not found"}

    # Paid users always allowed — check FIRST before anything else
    if profile.get("tier") == "paid":
        return {"allowed": True, "analyses_today": 0, "remaining": 999}

    today = date.today().isoformat()
    last_date = str(profile.get("last_analysis_date") or "")
    analyses_today = profile.get("analyses_today", 0)

    # Reset counter if it's a new day
    if last_date != today:
        analyses_today = 0
        supabase.table("profiles").update({
            "analyses_today": 0,
            "last_analysis_date": today
        }).eq("id", user_id).execute()

    if analyses_today >= MAX_FREE_ANALYSES:
        return {
            "allowed": False,
            "analyses_today": analyses_today,
            "remaining": 0
        }

    # Increment usage
    new_count = analyses_today + 1
    supabase.table("profiles").update({
        "analyses_today": new_count,
        "last_analysis_date": today
    }).eq("id", user_id).execute()

    return {
        "allowed": True,
        "analyses_today": new_count,
        "remaining": MAX_FREE_ANALYSES - new_count
    }