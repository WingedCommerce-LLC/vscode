#!/bin/bash

echo "🔧 Installing missing dependencies..."
pip install python-dotenv>=1.0.0 email-validator>=2.0.0

echo "🧪 Testing environment variable loading..."
cd /workspaces/overseer

# Test if environment variables are loaded
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
jwt_secret = os.getenv('JWT_SECRET')
if jwt_secret:
    print('✅ JWT_SECRET loaded successfully:', jwt_secret[:10] + '...')
else:
    print('❌ JWT_SECRET not found')
    exit(1)
"

echo "🚀 Starting API server..."
echo "If the server starts without errors, all dependency issues are fixed!"
echo "Press Ctrl+C to stop the server once you verify it's working."
echo ""
echo "Note: Make sure you're running this from the overseer directory!"
echo "Current directory: $(pwd)"

# Ensure we're in the overseer directory
if [[ ! -f "api/main.py" ]]; then
    echo "❌ Error: api/main.py not found. Make sure you're in the overseer directory."
    echo "Run: cd /workspaces/overseer"
    exit 1
fi

uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
