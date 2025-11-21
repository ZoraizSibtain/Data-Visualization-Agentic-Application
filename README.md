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
- Python 3.9+
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

3.  **Initialize Database** (using Go)
    ```bash
    cd src/go
    go mod init robotvacuum
    go get github.com/lib/pq
    go run create_schema.go
    go run ingest_masterdata.go
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
| `src/go/` | High-performance database initialization scripts. |

## 💡 Example Queries

Try these in the chat interface:
- *"Show me the top 5 selling products by revenue"*
- *"What is the average delivery time for each carrier?"*
- *"Plot the daily sales trend for the last 30 days"*
- *"Which warehouse has the most stock?"*

## 📚 Documentation

For a deep dive into the architecture and data flow, check out [PROJECT_DETAILS.md](PROJECT_DETAILS.md).

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
