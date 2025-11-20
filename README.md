# Robot Vacuum Depot Analytics

A Data Visualization Agentic Application that enables natural language query processing and automated chart generation.

## Setup Instructions

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 15+
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
```bash
# Ensure PostgreSQL is running, then load data
python -m data_processing.data_loader
```

### 5. Run Application
```bash
streamlit run app.py
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
