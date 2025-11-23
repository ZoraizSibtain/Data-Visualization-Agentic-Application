# Agentic Data Analysis

An AI-powered data analysis platform that transforms natural language questions into SQL queries, automated visualizations, and comprehensive reports.

## Features

### Core Capabilities
- **Natural Language to SQL** - Ask questions in plain English; the AI generates optimized SQL queries
- **Auto-Visualization** - Automatic Plotly chart generation with vibrant color schemes
- **Smart Query Memory** - Save, organize, and revisit your analysis sessions
- **PDF Report Generation** - Export queries with visualizations to shareable PDF reports

### User Interface
- **Organized Sidebar** - Clean navigation with collapsible database controls
- **Chat Sessions** - Multiple conversation threads with full history
- **Query History** - Visual card-based grid view (4-column layout) with filtering
- **One-Click Sample Queries** - Pre-built examples that run immediately in chat

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL database
- OpenAI API key

### Installation

1. **Clone and install dependencies**
```bash
cd SRC
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/robot_vacuum_depot
OPENAI_API_KEY=your-api-key-here
```

3. **Setup PostgreSQL database**
```bash
# Create database
createdb robot_vacuum_depot

# Initialize schema and load sample data
python setup_database.py
```

To reset with fresh data:
```bash
python setup_database.py --reset
```

4. **Run the application**
```bash
streamlit run Home.py
```

The app will open at `http://localhost:8501`

## Usage Guide

### Getting Started
1. Enter your OpenAI API key in the sidebar (Database > API Configuration)
2. Upload a CSV file or use the pre-loaded sample dataset
3. Start asking questions in the Chat interface

### Sample Queries

**Visualization Queries:**
- "Plot a line chart of total monthly revenue"
- "What is the percentage distribution of delivery statuses?"
- "Compare average shipping cost by carrier"
- "Plot the average review rating per manufacturer"

**Data Analysis Queries:**
- "Which robot vacuum models have the most delayed deliveries in Chicago?"
- "Which warehouses are below their restock threshold?"
- "What are the top 10 products by total revenue?"
- "List customers with the most orders"

### Working with Results
- **Save Queries** - Click the save button on any response
- **Export PDF** - Generate reports from saved queries
- **View History** - Browse past queries in a visual card grid
- **Provide Feedback** - Rate responses with thumbs up/down

## Project Structure

```
SRC/
├── Home.py                    # Landing page with navigation
├── config.py                  # Configuration and environment variables
├── setup_database.py          # Database initialization script
├── pages/
│   ├── 1_💬_Chat.py          # Main chat interface
│   ├── 2_📜_History.py       # Query history with card grid
│   ├── 3_💾_Saved_Queries.py # Saved queries and PDF export
│   └── 4_📊_Performance_Metrics.py
├── database/
│   ├── DatabaseManager.py     # Database connection handling
│   ├── query_storage.py       # Query persistence
│   ├── csv_ingestion.py       # CSV file loading
│   ├── etl_3nf.py            # ETL pipeline
│   └── schema_3nf.py         # Database schema
├── agents/
│   ├── workflow_manager.py    # LangGraph workflow
│   └── python_repl_tool.py   # Safe code execution
├── utils/
│   ├── prompts.py            # LLM prompts and examples
│   ├── pdf_generator.py      # PDF report generation
│   ├── sql_extractor.py      # SQL parsing utilities
│   └── sql_validator.py      # Security validation
└── data/                      # Sample datasets
```

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.12+
- **Database**: PostgreSQL with SQLAlchemy
- **AI/ML**: OpenAI GPT-4o-mini, LangChain, LangGraph
- **Visualization**: Plotly with custom color palettes
- **PDF Generation**: ReportLab with Kaleido for chart images

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |

### Optional: PDF Charts

To include visualizations in PDF reports, install Kaleido:
```bash
pip install kaleido
```

## Development

### Adding New Features

1. **New Pages** - Add to `pages/` directory with numbered prefix
2. **Custom Prompts** - Modify `utils/prompts.py`
3. **Database Schema** - Update `database/schema_3nf.py`

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Keep functions focused and documented

## Troubleshooting

### Common Issues

**Database Connection Error**
- Verify PostgreSQL is running
- Check DATABASE_URL in `.env`
- Ensure database exists: `createdb robot_vacuum_depot`

**Charts Not Appearing in PDF**
- Install kaleido: `pip install kaleido`
- Check that figure_json is being saved with queries

**API Key Issues**
- Verify OPENAI_API_KEY in `.env` or sidebar input
- Check API key has sufficient credits

## License

MIT License
