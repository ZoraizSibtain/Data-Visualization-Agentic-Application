# 📊 Agentic Data Analysis Application
Version 3.0

An intelligent data analysis application powered by LangChain agents and Streamlit. Upload CSV files and ask questions in natural language to get instant visualizations and insights.

## ✨ Features & Functions

### 🧠 Intelligent Analysis
- **Natural Language Processing**: Ask complex questions in plain English (e.g., "Show me sales trends for the last quarter").
- **Multi-Agent Orchestration**: A coordinated system of AI agents handles SQL generation, Python code execution, and data visualization.
- **Context Awareness**: The system remembers previous interactions within a session for seamless follow-up questions.

### 📊 Advanced Visualization
- **Auto-Plotting**: Automatically selects the most suitable chart type (Bar, Line, Scatter, Pie, Heatmap, etc.) based on the data.
- **Interactive Charts**: Fully interactive Plotly visualizations with zoom, pan, and hover details.
- **Customization**: Charts are styled with a premium, dark-mode aesthetic.

### 💾 Data & Session Management
- **Dynamic CSV Ingestion**: Upload any CSV file; the system automatically detects schemas and data types.
- **Saved Queries**: Bookmark important insights and access them later in a dedicated dashboard.
- **History Tracking**: Review past analysis sessions and search through your query history.
- **PDF Reporting**: Generate professional PDF reports including your charts and insights.

### 🛠️ Technical Capabilities
- **Secure Execution**: Python code runs in a sandboxed environment.
- **Error Recovery**: Self-correcting agents that can fix SQL syntax errors or code bugs automatically.
- **Performance Monitoring**: Track query execution times and user satisfaction metrics.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API Key

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd /Users/zibtain/Downloads/HW/SRC
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Key (Optional)**
   
   Create a `.env` file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
   
   *Note: You can also enter the API key directly in the app's sidebar*

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   
   The app will automatically open at `http://localhost:8501`

## 📖 Usage

### First Time Setup

1. Click **"Initialize Default Database"** in the sidebar to load the sample RobotVacuum dataset
2. Enter your OpenAI API key in the sidebar (or set it in `.env`)

### Analyzing Data

Ask questions in natural language:
- "Show me the top 10 products by sales"
- "What's the trend of revenue over time?"
- "Compare sales across different categories"
- "Show the distribution of product prices"

The AI will automatically:
1. Generate appropriate SQL queries
2. Execute them against your database
3. Create beautiful, interactive visualizations

### Uploading Custom Data

1. Click **"Upload CSV"** in the sidebar
2. Select your CSV file
3. Click **"Process CSV"**
4. Start asking questions about your data!

## 🏗️ Architecture

```
SRC/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration settings
├── requirements.txt            # Dependencies
├── database/
│   ├── DatabaseManager.py      # Dynamic schema inspection
│   ├── csv_ingestion.py        # CSV upload handler
│   └── database_setup.py       # Default data setup
├── agents/
│   ├── workflow_manager.py     # Multi-agent orchestration
│   └── python_repl_tool.py     # Safe code execution
├── utils/
│   └── prompts.py              # LLM prompts
└── data/
    ├── robot_vacuum.db         # SQLite database
    └── RobotVacuumDepot_MasterData.csv
```

## 🎯 Key Components

### DatabaseManager
- Dynamic schema inspection using SQLAlchemy
- Supports any CSV structure
- Automatic type inference

### WorkflowManager
- Multi-agent orchestration
- Code generation and execution
- Error recovery with retries

### PythonREPL Tool
- Safe Python code execution
- Pre-configured with pandas, plotly, SQLAlchemy
- Database connection injection

## 🎨 Visualization Types

The AI automatically selects the best visualization:
- **Bar Charts**: Comparisons and rankings
- **Line Charts**: Trends over time
- **Scatter Plots**: Relationships between variables
- **Pie Charts**: Proportions and percentages
- **Histograms**: Distributions
- **Box Plots**: Statistical distributions
- **Heatmaps**: Correlations

## 🔧 Configuration

Edit `config.py` to customize:
- Database paths
- LLM model (default: gpt-4o-mini)
- Temperature settings
- Max iterations for error recovery

## 🛡️ Security Notes

- API keys are never logged or stored
- Python code execution is sandboxed
- SQL queries are generated by AI (review in UI)

## 📝 Example Questions

**Sales Analysis:**
- "What are the top 5 best-selling products?"
- "Show monthly sales trends"
- "Compare revenue by category"

**Statistical Analysis:**
- "What's the average price by brand?"
- "Show the distribution of ratings"
- "Find outliers in the sales data"

**Comparative Analysis:**
- "Compare performance across regions"
- "Show year-over-year growth"
- "Which category has the highest margin?"

## 🔄 Changelog (vs Legacy Version)

This version represents a major architectural overhaul from the previous iteration (`old src`):

- **Architecture**: Transitioned from a monolithic script to a modular **Streamlit Multipage Application** for better scalability and navigation.
- **UI/UX**: Implemented a **Premium Design System** with custom CSS, vibrant gradients, and improved layout hierarchy.
- **Agent System**: Refactored the `agentic_processor` into a streamlined `agents/` directory with clearer separation of concerns (Workflow Manager, Python REPL).
- **Database**: Enhanced `DatabaseManager` with robust CSV ingestion, automatic type inference, and persistent query storage.
- **New Features**: Added PDF reporting, saved queries dashboard, and performance metrics tracking.

## 🤝 Contributing

This project follows the architecture specified in the COMPLETE_RECREATE_PROMPT with:
- Dynamic schema handling (no hardcoded queries)
- Visualization-first approach
- LangChain PythonREPLTool integration
- Multi-agent workflow patterns

## 📄 License

MIT License

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [LangChain](https://langchain.com/)
- Visualizations by [Plotly](https://plotly.com/)
