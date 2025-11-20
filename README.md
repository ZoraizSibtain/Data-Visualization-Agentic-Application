# Robot Vacuum Depot Analytics

A Data Visualization Agentic Application that enables natural language query processing and automated chart generation.

## Setup Instructions

### 1. Prerequisites
- Python
- PostgreSQL
- OpenAI API Key

### 2. Install Dependencies
```bash
cd src
pip install -r requirements.txt
# incase that does work, this worked for me
pip3 install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your-api-key-here
```

### 4. Setup Database

#### Option A: Using Go (recommended)
```bash
# Ensure PostgreSQL is running
# Navigate to the Go source directory
cd src/go

# Initialize Go module and install PostgreSQL driver
go mod init robotvacuum
go get github.com/lib/pq

# Test Connection
go run main.go

# Create/recreate the database schema (drops existing data)
go run create_schema.go

# Load the master data from CSV
go run ingest_masterdata.go
```

### 5. Run Application
```bash
python3 -m streamlit run app.py
```

## Features
- Natural language query processing
- Automatic SQL generation using GPT-4o-mini
- Smart chart type detection
- Support for: Line, Bar, Pie, Scatter, and Table views
- Interactive Plotly visualizations
- CSV export capability

## Example Queries
- "Plot a line chart of total monthly revenue"
- "What is the percentage distribution of delivery statuses?"
- "Which manufacturer has the best average review rating?"
- "Compare average shipping cost by carrier"