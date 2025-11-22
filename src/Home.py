"""
Home Page - Landing page for Agentic Data Analysis
"""
import streamlit as st
import os
from dotenv import load_dotenv
from database.query_storage import QueryStorage
from database.DatabaseManager import DatabaseManager
from database.database_setup import initialize_database
import config

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Agentic Data Analysis",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
    <style>
    /* Global Styles */
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Typography */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Cards */
    .stCard {
        background-color: #262730;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .stCard:hover {
        transform: translateY(-5px);
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #FF4B4B;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(45deg, #FF4B4B, #FF914D);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        box-shadow: 0 5px 15px rgba(255, 75, 75, 0.4);
        transform: scale(1.02);
    }
    
    /* Custom Classes */
    .feature-card {
        background-color: #1E1E1E;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #333;
        height: 100%;
    }
    .step-number {
        font-size: 2rem;
        font-weight: bold;
        color: #FF4B4B;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

def init_database():
    """Initialize database if needed"""
    if 'database_initialized' not in st.session_state:
        try:
            initialize_database()
            st.session_state.database_initialized = True
            st.session_state.db_manager = DatabaseManager()
        except:
            pass

# Initialize
init_database()

# Hero Section
col1, col2 = st.columns([2, 1])

with col1:
    st.title("Agentic Data Analysis")
    st.markdown("### 🚀 Unlock Insights with AI-Powered Conversations")
    st.markdown("""
    <div style='font-size: 1.2rem; color: #cccccc; margin-bottom: 2rem;'>
    Transform your raw data into actionable intelligence. Upload your CSVs, ask questions in plain English, 
    and watch as our multi-agent system generates SQL, executes code, and visualizes results instantly.
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Start Analyzing Now ➡️"):
        st.switch_page("pages/1_💬_Chat.py")

with col2:
    # Placeholder for a hero image or dynamic element
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%); 
                border-radius: 20px; padding: 2rem; text-align: center; border: 1px solid #333;'>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>📊</div>
        <div style='font-size: 1.5rem; font-weight: bold; margin-bottom: 0.5rem;'>Smart Analytics</div>
        <div style='color: #888;'>Powered by LLMs</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Key Features Section
st.header("✨ Powerful Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>💬 Natural Language</h3>
        <p>Forget complex SQL queries. Just ask "What are the top selling products?" and get instant answers.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Auto-Visualization</h3>
        <p>The system automatically selects the best chart type for your data, from bar charts to heatmaps.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>💾 Smart Memory</h3>
        <p>Save your favorite queries, export reports to PDF, and track your analysis history effortlessly.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Performance Stats
st.header("📈 System Performance")
col1, col2, col3, col4 = st.columns(4)

try:
    query_storage = QueryStorage()
    metrics = query_storage.get_performance_metrics()
    
    with col1:
        st.metric("Total Queries", metrics['total_queries'], delta="All time")
    with col2:
        st.metric("Saved Insights", metrics['saved_count'], delta="Bookmarked")
    with col3:
        st.metric("Avg Speed", f"{metrics['avg_execution_time']:.2f}s", delta="Response Time")
    with col4:
        satisfaction = metrics['satisfaction_rate']
        st.metric("User Satisfaction", f"{satisfaction:.1f}%", delta="Feedback")
except:
    st.info("Connect a database to see live metrics.")

st.divider()

# How It Works
st.header("🛠️ How It Works")
col1, col2, col3, col4 = st.columns(4)

steps = [
    ("1", "Upload Data", "Upload your CSV file. The system automatically detects schema and types."),
    ("2", "Ask Questions", "Type your questions in plain English. No coding required."),
    ("3", "Get Insights", "View generated SQL, Python code, and interactive visualizations."),
    ("4", "Save & Export", "Save key insights and generate professional PDF reports.")
]

for col, (num, title, desc) in zip([col1, col2, col3, col4], steps):
    with col:
        st.markdown(f"""
        <div style='text-align: center;'>
            <div class="step-number">{num}</div>
            <h4 style='color: #fafafa;'>{title}</h4>
            <p style='color: #aaaaaa; font-size: 0.9rem;'>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

# Database Status Footer
st.divider()
if st.session_state.get('database_initialized'):
    st.success(f"✅ System Ready | Active Database: {st.session_state.db_manager.get_table_names()[0] if st.session_state.db_manager.get_table_names() else 'None'}")
else:
    st.warning("⚠️ System Standby | Initialize database to begin")
