import os
import random
from datetime import timedelta

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from pydantic import BaseModel

load_dotenv(".env.local")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
API_KEY = os.getenv("LIVEKIT_API_KEY")
API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")


class ConnectionDetails(BaseModel):
    serverUrl: str
    roomName: str
    participantName: str
    participantToken: str


def create_participant_token(identity: str, room_name: str) -> str:
    """Create a LiveKit access token for a participant"""
    token = api.AccessToken(API_KEY, API_SECRET)
    token.with_identity(identity).with_name(identity).with_ttl(timedelta(minutes=15))
    token.with_grants(
        api.VideoGrants(
            room=room_name,
            room_join=True,
            can_publish=True,
            can_publish_data=True,
            can_subscribe=True,
        )
    )
    return token.to_jwt()


@app.get("/api/connection-details", response_model=ConnectionDetails)
async def get_connection_details():
    """Generate connection details for a LiveKit room"""
    try:
        if not LIVEKIT_URL:
            raise HTTPException(status_code=500, detail="LIVEKIT_URL is not defined")
        if not API_KEY:
            raise HTTPException(
                status_code=500, detail="LIVEKIT_API_KEY is not defined"
            )
        if not API_SECRET:
            raise HTTPException(
                status_code=500, detail="LIVEKIT_API_SECRET is not defined"
            )

        # Generate participant identity and room name
        participant_identity = f"voice_assistant_user_{random.randint(0, 9999)}"
        room_name = f"voice_assistant_room_{random.randint(0, 9999)}"

        # Create participant token
        participant_token = create_participant_token(participant_identity, room_name)

        # Return connection details
        return ConnectionDetails(
            serverUrl=LIVEKIT_URL,
            roomName=room_name,
            participantToken=participant_token,
            participantName=participant_identity,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "LiveKit Agent API"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10001)
