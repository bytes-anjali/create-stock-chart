#!/usr/bin/env bash
set -e

echo "=== YT Multi-Channel Dashboard Setup ==="

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created backend/.env — review it if needed."
fi
if [ ! -f client_secret.json ]; then
  echo ""
  echo "ACTION REQUIRED: Place client_secret.json in backend/"
  echo "  1. Go to https://console.cloud.google.com/"
  echo "  2. APIs & Services > Credentials > Create OAuth 2.0 Client ID (Web application)"
  echo "  3. Add Authorized redirect URI: http://localhost:8000/api/auth/callback"
  echo "  4. Download JSON and save as backend/client_secret.json"
  echo ""
fi
cd ..

# Frontend
cd frontend
npm install
cd ..

echo ""
echo "=== Done ==="
echo "Start backend : cd backend && source .venv/bin/activate && uvicorn main:app --reload"
echo "Start frontend: cd frontend && npm run dev"
echo "Then open      http://localhost:5173"
