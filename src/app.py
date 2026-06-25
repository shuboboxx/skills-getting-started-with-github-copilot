"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Squad": {
        "description": "Team-based soccer training and matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["lisa@mergington.edu"]
    },
    "Swimming Team": {
        "description": "Swim practice and competitive meets",
        "schedule": "Mondays, Wednesdays, 5:00 PM - 6:30 PM",
        "max_participants": 18,
        "participants": ["alex@mergington.edu"]
    },
    "Art Workshop": {
        "description": "Hands-on studio art projects in painting and drawing",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["maya@mergington.edu"]
    },
    "Drama Club": {
        "description": "Acting, stagecraft, and performance rehearsal",
        "schedule": "Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["noah@mergington.edu"]
    },
    "Math Olympiad": {
        "description": "Advanced problem solving and competition prep",
        "schedule": "Tuesdays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["sophia@mergington.edu"]
    },
    "Science Club": {
        "description": "Hands-on experiments and science research projects",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["ethan@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Normalize email and validate
    normalized_email = email.strip().lower()

    # Prevent duplicate signups
    if normalized_email in [e.strip().lower() for e in activity.get("participants", [])]:
        raise HTTPException(status_code=400, detail="Student already signed up for this activity")

    # Enforce max participants limit
    max_p = activity.get("max_participants")
    if isinstance(max_p, int) and len(activity.get("participants", [])) >= max_p:
        raise HTTPException(status_code=400, detail="Activity is full")

    # Add student
    activity.setdefault("participants", []).append(normalized_email)
    return {"message": f"Signed up {normalized_email} for {activity_name}"}


@app.delete("/activities/{activity_name}/remove")
def remove_participant(activity_name: str, email: str):
    """Remove a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Normalize email
    normalized_email = email.strip().lower()

    # Check if participant exists
    participants = activity.get("participants", [])
    lower_participants = [p.strip().lower() for p in participants]

    if normalized_email not in lower_participants:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    # Remove participant (find original case version)
    idx = lower_participants.index(normalized_email)
    participants.pop(idx)

    return {"message": f"Removed {email} from {activity_name}"}
