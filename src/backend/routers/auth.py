"""
Authentication endpoints for the High School Management System API
"""

from fastapi import APIRouter, Header, HTTPException
from secrets import token_urlsafe
from typing import Dict, Any

from ..database import teachers_collection, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

active_sessions: Dict[str, str] = {}


def get_session_teacher(session_token: str) -> Dict[str, Any]:
    """Return the teacher associated with an active login session."""
    username = active_sessions.get(session_token)
    teacher = teachers_collection.find_one({"_id": username}) if username else None
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")
    return teacher


@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    session_token = token_urlsafe(32)
    active_sessions[session_token] = teacher["username"]

    # Return teacher information (excluding password)
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
        "session_token": session_token,
    }


@router.get("/check-session")
def check_session(x_session_token: str = Header()) -> Dict[str, Any]:
    """Check whether a server-issued login session is valid."""
    teacher = get_session_teacher(x_session_token)

    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
        "session_token": x_session_token,
    }


@router.post("/logout", status_code=204)
def logout(x_session_token: str = Header()) -> None:
    """End an active login session."""
    active_sessions.pop(x_session_token, None)
