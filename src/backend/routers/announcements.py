"""Announcement endpoints for the High School Management System API."""

from datetime import date
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from ..database import announcements_collection
from .auth import get_session_teacher

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementInput(BaseModel):
    """Fields accepted when creating or updating an announcement."""

    message: str = Field(min_length=1, max_length=500)
    expiration_date: date
    start_date: Optional[date] = None


def require_teacher(session_token: str) -> None:
    """Require a valid server-issued login session."""
    get_session_teacher(session_token)


def validate_dates(announcement: AnnouncementInput) -> None:
    """Ensure an announcement does not expire before it starts."""
    if not announcement.message.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message is required",
        )
    if (
        announcement.start_date
        and announcement.expiration_date < announcement.start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Expiration date must be on or after the start date",
        )


def serialize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a MongoDB announcement document into JSON-safe data."""
    return {
        "id": str(document["_id"]),
        "message": document["message"],
        "start_date": document.get("start_date"),
        "expiration_date": document["expiration_date"],
    }


def parse_announcement_id(announcement_id: str) -> ObjectId:
    """Parse an announcement id without leaking database errors."""
    if not ObjectId.is_valid(announcement_id):
        raise HTTPException(status_code=404, detail="Announcement not found")
    return ObjectId(announcement_id)


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Return announcements active today for public display."""
    today = date.today().isoformat()
    query = {
        "expiration_date": {"$gte": today},
        "$or": [
            {"start_date": None},
            {"start_date": {"$exists": False}},
            {"start_date": {"$lte": today}},
        ],
    }
    return [
        serialize_announcement(document)
        for document in announcements_collection.find(query).sort("expiration_date", 1)
    ]


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(
    x_session_token: str = Header(),
) -> List[Dict[str, Any]]:
    """Return all announcements for signed-in users to manage."""
    require_teacher(x_session_token)
    return [
        serialize_announcement(document)
        for document in announcements_collection.find().sort("expiration_date", -1)
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement: AnnouncementInput,
    x_session_token: str = Header(),
) -> Dict[str, Any]:
    """Create an announcement as a signed-in user."""
    require_teacher(x_session_token)
    validate_dates(announcement)
    document = {
        "message": announcement.message.strip(),
        "start_date": (
            announcement.start_date.isoformat() if announcement.start_date else None
        ),
        "expiration_date": announcement.expiration_date.isoformat(),
    }
    result = announcements_collection.insert_one(document)
    document["_id"] = result.inserted_id
    return serialize_announcement(document)


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    announcement: AnnouncementInput,
    x_session_token: str = Header(),
) -> Dict[str, Any]:
    """Update an announcement as a signed-in user."""
    require_teacher(x_session_token)
    validate_dates(announcement)
    object_id = parse_announcement_id(announcement_id)
    updates = {
        "message": announcement.message.strip(),
        "start_date": (
            announcement.start_date.isoformat() if announcement.start_date else None
        ),
        "expiration_date": announcement.expiration_date.isoformat(),
    }
    result = announcements_collection.update_one(
        {"_id": object_id}, {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    updates["_id"] = object_id
    return serialize_announcement(updates)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: str,
    x_session_token: str = Header(),
) -> None:
    """Delete an announcement as a signed-in user."""
    require_teacher(x_session_token)
    result = announcements_collection.delete_one(
        {"_id": parse_announcement_id(announcement_id)}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")