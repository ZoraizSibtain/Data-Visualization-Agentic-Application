# 🤖 Robot Vacuum Depot Analytics

**Robot Vacuum Depot Analytics** is an advanced **Agentic BI Tool** that transforms natural language into actionable insights. Built with **LangGraph** and **Streamlit**, it empowers users to query their supply chain data without writing a single line of SQL.

---

## ✨ Key Features

- **🗣️ Natural Language Interface**: Ask "Why are deliveries delayed in Chicago?" and get an answer.
- **📊 Auto-Visualization**: Automatically selects the best chart (Bar, Line, Scatter, Pie) for your data.
- **⚡ Smart Caching**: Caches generated SQL to deliver sub-second responses for recurring queries.
- **📈 Performance Analytics**: Built-in dashboard to monitor query latency and system health.
- **🔄 History & Replay**: Access and re-run your entire query history.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL
- OpenAI API Key

### Installation

1.  **Clone & Setup**
    ```bash
    cd src
    pip3 install -r requirements.txt
    ```

2.  **Configure Environment**
    ```bash
    cp .env.example .env
    # Edit .env with your OPENAI_API_KEY and DB credentials
    ```

3.  **Initialize Database**
    ```bash
    python3 setup.py
    ```

4.  **Run the App**
    ```bash
    cd src
    streamlit run app.py
    or
    python3 -m streamlit run app.py
    ```

## 📂 Project Structure

| Directory | Description |
|-----------|-------------|
| `src/app.py` | Main Streamlit application entry point. |
| `src/agentic_processor/` | Orchestrates the query flow and caching logic. |
| `src/my_agent/` | Core LangGraph agent definitions (SQL generation, execution). |
| `src/visualization/` | Plotly-based chart rendering engine. |
| `src/backend/` | Stores persistent data (saved queries, test results). |
| `src/database_setup.py` | Database initialization and ETL pipeline. |
| `src/setup.py` | Project setup and dependency installation script. |

## 💡 Example Queries

Try these in the chat interface:
- *"Show me the top 5 selling products by revenue"*
- *"What is the average delivery time for each carrier?"*
- *"Plot the daily sales trend for the last 30 days"*
- *"Which warehouse has the most stock?"*

## 📚 Documentation

For a deep dive into the architecture and data flow, check out [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md).

---

## 📋 Changelog

### v2.0.0 (Latest)

**New Features**
- **RAG Layer**: Added Retrieval Augmented Generation (`RAGLayer.py`) for enhanced SQL generation with semantic search, few-shot learning examples, and business context injection
- **Saved Queries Mode**: New UI mode to save, view, and manage favorite queries with grid layout
- **PDF Export**: Export selected saved queries to PDF reports
- **Chart Highlighting**: Bar charts now highlight maximum values when queries contain keywords like "highest", "top", "best"

**Improvements**
- Enhanced error handling throughout SQLAgent (parse_question, generate_sql, validate_sql, format_results)
- Improved Analytics dashboard layout with better timing displays
- Added save/star functionality to History and Dashboard modes
- Better chart rendering with query-aware context

**Technical Changes**
- Removed `data_processing/` directory (consolidated functionality)
- Added `.env.example` template for easier setup
- Updated requirements with new RAG dependencies (OpenAI embeddings, numpy)
- Persistent saved queries via `saved_queries.json`

---

## 🔧 Troubleshooting

### Common Issues

**1. "Database not found" or Connection Errors**
- Ensure PostgreSQL is running.
- Check your `.env` file credentials (`POSTGRES_USER`, `POSTGRES_PASSWORD`, etc.).
- Run `python3 src/setup.py` again to rebuild the schema.

**2. "OpenAI API Key missing"**
- Make sure you have created a `.env` file from `.env.example`.
- Verify your API key is valid and has access to `gpt-4o-mini`.

**3. `pip install` fails**
- Ensure you are using Python 3.9 or higher.
- Try upgrading pip: `pip install --upgrade pip`.

**4. Charts not displaying**
- Ensure `kaleido` is installed (included in requirements) for static image generation.
- Check if the query returned data (look for "Rows: 0" in the UI).

### Resetting the Environment
If you need to start fresh:
1. Drop the `robot_vacuum_depot` schema in your database tool.
2. Run `python3 src/setup.py`.
