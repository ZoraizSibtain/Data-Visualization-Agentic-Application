import streamlit as st
import os

def render_sidebar():
    """Render the shared sidebar navigation for all pages."""
    with st.sidebar:
        st.title("🤖 Agentic Data")

        # Navigation Section
        st.markdown('<div style="font-weight: bold; color: #ccc; margin-bottom: 0.5rem; text-transform: uppercase; font-size: 0.8rem;">Navigation</div>', unsafe_allow_html=True)
        st.page_link("Home.py", label="Home", icon="🏠")
        st.page_link("pages/1_💬_Chat.py", label="Chat Interface", icon="💬")
        st.page_link("pages/2_📜_History.py", label="Query History", icon="📜")
        st.page_link("pages/3_💾_Saved_Queries.py", label="Saved Queries", icon="💾")
        st.page_link("pages/4_📊_Performance_Metrics.py", label="Metrics", icon="📊")

        st.markdown("---")
