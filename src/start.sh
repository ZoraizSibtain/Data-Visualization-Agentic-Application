#!/bin/bash

# Agentic Data Analysis - Quick Start Script

echo "🚀 Starting Agentic Data Analysis Application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check if database exists
if [ ! -f "data/robot_vacuum.db" ]; then
    echo "🗄️  Initializing database..."
    python -c "from database.database_setup import initialize_database; print(initialize_database())"
fi

# Check for API key
if [ -z "$OPENAI_API_KEY" ] && [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  WARNING: No OpenAI API key found!"
    echo "   You can either:"
    echo "   1. Set OPENAI_API_KEY environment variable"
    echo "   2. Create a .env file (see .env.example)"
    echo "   3. Enter it in the app's sidebar"
    echo ""
fi

# Launch Streamlit
echo ""
echo "✨ Launching application..."
echo "   The app will open in your browser at http://localhost:8501"
echo ""
streamlit run app.py
