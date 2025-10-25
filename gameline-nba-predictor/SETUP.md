# GameLine Setup Guide

This guide will help you connect the GameLine Next.js frontend to your Flask backend.

## Prerequisites

- Node.js 18+ installed
- Python 3.8+ installed
- Your Flask backend code (server.py and related files)

## Step 1: Install Flask CORS Support

Your Flask backend needs to allow cross-origin requests from the Next.js dev server.

1. Install Flask-CORS:
\`\`\`bash
pip install flask-cors
\`\`\`

2. Update your `server.py` to enable CORS:

\`\`\`python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# ... rest of your Flask code
\`\`\`

## Step 2: Start Your Flask Backend

1. Navigate to your Flask backend directory
2. Install all required dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. Start the Flask server (it should run on port 5001):
\`\`\`bash
python server.py
\`\`\`

You should see output like:
\`\`\`
* Running on http://127.0.0.1:5001
\`\`\`

## Step 3: Configure the Frontend

The frontend is already configured to connect to `http://localhost:5001` by default.

If your Flask server runs on a different port, create a `.env.local` file in the root directory:

\`\`\`env
NEXT_PUBLIC_API_URL=http://localhost:YOUR_PORT
\`\`\`

## Step 4: Start the Next.js Frontend

1. Install dependencies (if not already done):
\`\`\`bash
npm install
\`\`\`

2. Start the development server:
\`\`\`bash
npm run dev
\`\`\`

3. Open your browser to `http://localhost:3000`

## Troubleshooting

### CORS Errors
If you see CORS errors in the browser console:
- Make sure Flask-CORS is installed and configured correctly
- Verify the Flask server is running on port 5001
- Check that the origins in CORS config match your Next.js dev server URL

### Connection Refused
If you see "Connection refused" errors:
- Verify the Flask server is running: `curl http://localhost:5001/api/teams`
- Check the port number matches in both frontend and backend
- Make sure no firewall is blocking the connection

### API Errors
If predictions fail:
- Check the Flask server logs for error messages
- Verify all required environment variables are set in your Flask app
- Ensure the NBA API keys and database connections are configured

## Production Deployment

For production, you'll need to:

1. Deploy your Flask backend to a hosting service (Heroku, AWS, etc.)
2. Update the `NEXT_PUBLIC_API_URL` environment variable to point to your production API
3. Deploy your Next.js frontend to Vercel or another hosting platform

## API Endpoints Used

The frontend connects to these Flask endpoints:

- `GET /api/all-players` - Fetch all active NBA players
- `GET /api/teams` - Fetch all NBA teams
- `GET /api/player-details/<player_name>` - Get player details with headshot
- `GET /api/predict` - Generate prediction (query params: player_name, category, opponent_abbr, betting_line, season_type)
