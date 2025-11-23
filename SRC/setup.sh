#!/bin/bash

# Complete setup script for Agentic Data Analysis
# This script performs cleanup, installs requirements, sets up the database, and runs the app

set -e  # Exit on error

echo "=========================================="
echo "Agentic Data Analysis - Complete Setup"
echo "=========================================="
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Step 1: Cleanup
echo "Step 1: Cleaning up..."
echo "----------------------------------------"

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  ✓ Cleared Python cache"

# Clear Streamlit cache
rm -rf ~/.streamlit/cache 2>/dev/null || true
echo "  ✓ Cleared Streamlit cache"

# Clear temp files
rm -rf /tmp/*.csv 2>/dev/null || true
echo "  ✓ Cleared temp files"

echo ""

# Step 2: Install requirements
echo "Step 2: Installing requirements..."
echo "----------------------------------------"
pip install -r requirements.txt --quiet
echo "  ✓ Requirements installed"
echo ""

# Step 3: Reset and setup database
echo "Step 3: Setting up database..."
echo "----------------------------------------"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "  ⚠ Warning: .env file not found"
    echo "  Creating default .env file..."
    cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agentic_data
OPENAI_API_KEY=your_openai_api_key_here
EOF
    echo "  ✓ Created .env file (please update with your credentials)"
fi

# Run database setup with reset flag
python setup_database.py --reset
echo "  ✓ Database setup complete"
echo ""

# Step 4: Run Streamlit app
echo "Step 4: Starting Streamlit app..."
echo "=========================================="
echo ""
echo "Access the app at: http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run Home.py
