# Agentic Data Analysis

AI-powered data analysis platform with natural language queries, automatic visualizations, and smart memory.

## Features

- **Natural Language Queries**: Ask questions in plain English
- **Auto-Visualization**: Automatic Plotly chart generation
- **Smart Memory**: Save queries, track history, export PDF reports
- **Session Management**: Multiple chat sessions

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL and OpenAI credentials.

### 3. Setup PostgreSQL Database

```bash
# Create database
createdb robot_vacuum_depot

# Or using psql
psql -c "CREATE DATABASE robot_vacuum_depot;"
```

### 4. Initialize Database

```bash
python setup_database.py
```

To reset and reload data:
```bash
python setup_database.py --reset
```

### 5. Run the Application

```bash
streamlit run Home.py
```

## Usage

1. Enter your OpenAI API key in the sidebar
2. Upload a CSV file or use the default dataset
3. Ask questions in natural language
4. View generated visualizations and SQL queries
5. Save queries and export PDF reports

## Sample Queries

**Visualization:**
- "Plot a line chart of total monthly revenue"
- "What is the percentage distribution of delivery statuses?"
- "Compare average shipping cost by carrier"

**Tabular:**
- "Which robot vacuum models have the most delayed deliveries?"
- "Which warehouses are below their restock threshold?"

## Project Structure

```
SRC/
├── Home.py                    # Landing page
├── config.py                  # Configuration
├── setup_database.py          # Database initialization
├── pages/                     # Streamlit pages
├── database/                  # Database modules
├── agents/                    # AI workflow
├── utils/                     # Utilities
└── data/                      # Sample data
```

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.12+
- **Database**: PostgreSQL + SQLAlchemy
- **AI**: OpenAI GPT-4o-mini, LangChain, LangGraph
- **Visualization**: Plotly
