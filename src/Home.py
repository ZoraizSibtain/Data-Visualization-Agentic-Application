import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.query_storage import QueryStorage
from config import DATABASE_URL

# Page config
st.set_page_config(
    page_title="Agentic Data Analysis",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border: 1px solid #3d3d5c;
    }
    .feature-title {
        color: #667eea;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        color: #ccc;
        font-size: 0.9rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #2d2d44 0%, #1e1e2e 100%);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #3d3d5c;
    }
    .step-number {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
        font-weight: bold;
    }
    .query-template {
        background: #1e1e2e;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
        cursor: pointer;
    }
    .query-template:hover {
        background: #2d2d44;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">Agentic Data Analysis</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-powered data analysis with natural language queries</p>', unsafe_allow_html=True)

# Feature cards
st.markdown("### Key Features")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">💬 Natural Language</div>
        <div class="feature-desc">Ask questions in plain English. Our AI translates your queries into optimized SQL.</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">📊 Auto-Visualization</div>
        <div class="feature-desc">Get beautiful Plotly charts automatically generated for your data insights.</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">🧠 Smart Memory</div>
        <div class="feature-desc">Save queries, track history, and export PDF reports for later reference.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Performance metrics
st.markdown("### Platform Metrics")
try:
    query_storage = QueryStorage(DATABASE_URL)
    metrics = query_storage.get_performance_metrics()
    query_storage.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Queries", metrics['total_queries'])
    with col2:
        st.metric("Avg Execution Time", f"{metrics['avg_execution_time']:.2f}s")
    with col3:
        st.metric("Satisfaction Rate", f"{metrics['satisfaction_rate']:.1f}%")
    with col4:
        st.metric("Saved Queries", metrics['saved_count'])
except Exception as e:
    st.info("Connect to database to see metrics")

st.markdown("---")

# How it works
st.markdown("### How It Works")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <span class="step-number">1</span> **Upload Data**

    Upload your CSV file or use our sample dataset.
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <span class="step-number">2</span> **Ask Questions**

    Type your question in natural language.
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <span class="step-number">3</span> **Get Insights**

    View SQL, code, and visualizations.
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <span class="step-number">4</span> **Save & Export**

    Save queries and generate reports.
    """, unsafe_allow_html=True)

st.markdown("---")

# Sample queries
st.markdown("### Sample Queries")

tab1, tab2 = st.tabs(["📊 Visualization Queries", "📋 Tabular Queries"])

with tab1:
    st.markdown("""
    <div class="query-template">
        Plot a line chart of total monthly revenue
    </div>
    <div class="query-template">
        What is the percentage distribution of delivery statuses?
    </div>
    <div class="query-template">
        Plot the average review rating per manufacturer
    </div>
    <div class="query-template">
        Compare average shipping cost by carrier
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown("""
    <div class="query-template">
        Which robot vacuum models have the most delayed deliveries in Chicago?
    </div>
    <div class="query-template">
        Which warehouses are currently below their restock threshold?
    </div>
    <div class="query-template">
        What are the top 10 products by total revenue?
    </div>
    <div class="query-template">
        List customers with the most orders
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Call to action
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("### Ready to start analyzing?")
    if st.button("🚀 Go to Chat", use_container_width=True, type="primary"):
        st.switch_page("pages/1_💬_Chat.py")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <small>Powered by OpenAI GPT-4o-mini | LangChain | LangGraph</small>
</div>
""", unsafe_allow_html=True)
