# API Usage Guide

## Get Connection Details

### Endpoint
```
POST /api/connection-details
```

### Description
Retrieve LiveKit connection details including server URL, room name, participant name, and access token.

### Request Headers
- `Content-Type: application/json`

### Request Body

#### Without Agent Configuration
```bash
curl -X POST http://localhost:8000/api/connection-details \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### With Agent Configuration
```bash
curl -X POST http://localhost:8000/api/connection-details \
  -H "Content-Type: application/json" \
  -d '{
    "room_config": {
      "agents": [
        {
          "agent_name": "your-agent-name"
        }
      ]
    }
  }'
```

### Response Format

#### Success Response (200 OK)
```json
{
  "serverUrl": "wss://your-livekit-server.com",
  "roomName": "voice_assistant_room_1234",
  "participantName": "user",
  "participantToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Response Headers
- `Cache-Control: no-store`

#### Error Response (500 Internal Server Error)
```json
{
  "detail": "Error message describing what went wrong"
}
```

#### Pretty-printed Response

Use `jq` to show the pretty-printed response. [Download jq here.](https://jqlang.org/download/)

```bash
curl -X POST http://localhost:8000/api/connection-details \
  -H "Content-Type: application/json" \
  -d '{}' | jq
```

### Environment Variables Required

The server requires the following environment variables to be set:

- `LIVEKIT_URL` - Your LiveKit server URL
- `LIVEKIT_API_KEY` - Your LiveKit API key
- `LIVEKIT_API_SECRET` - Your LiveKit API secret

These should be configured in `.env.local` file in the project root.

### Notes

- Room names and participant identities are randomly generated for each request
- Tokens have a 15-minute TTL (time to live)
- The endpoint does not cache responses (`Cache-Control: no-store`)
- If `agent_name` is not provided, the token will be created without agent configuration
