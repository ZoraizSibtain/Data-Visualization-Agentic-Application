"""
History Page - View all query history
"""
import streamlit as st
from database.query_storage import QueryStorage
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta

st.set_page_config(
    page_title="History - Agentic Data Analysis",
    page_icon="📜",
    layout="wide"
)

# Initialize
if 'query_storage' not in st.session_state:
    st.session_state.query_storage = QueryStorage()

st.title("📜 Query History")
st.markdown("View all your past queries and results")

# Filters
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    search_term = st.text_input("🔍 Search queries", placeholder="Enter keywords...")

with col2:
    days_filter = st.selectbox(
        "📅 Time Range",
        ["All Time", "Last 24 Hours", "Last 7 Days", "Last 30 Days"]
    )

with col3:
    limit = st.number_input("Show", min_value=10, max_value=500, value=50, step=10)

st.divider()

# Get queries
try:
    all_queries = st.session_state.query_storage.get_all_queries(limit=limit)
    
    # Apply filters
    filtered_queries = all_queries
    
    # Search filter
    if search_term:
        filtered_queries = [
            q for q in filtered_queries
            if search_term.lower() in q['user_question'].lower()
        ]
    
    # Time filter
    if days_filter != "All Time":
        days_map = {
            "Last 24 Hours": 1,
            "Last 7 Days": 7,
            "Last 30 Days": 30
        }
        cutoff_date = datetime.now() - timedelta(days=days_map[days_filter])
        filtered_queries = [
            q for q in filtered_queries
            if q['timestamp'] >= cutoff_date
        ]
    
    # Display results
    st.markdown(f"### Found {len(filtered_queries)} queries")
    
    if not filtered_queries:
        st.info("No queries found. Try adjusting your filters or ask some questions in the Chat page!")
    else:
        for query in filtered_queries:
            with st.expander(f"🕐 {query['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {query['user_question'][:80]}..."):
                # Question
                st.markdown(f"**Question:** {query['user_question']}")
                
                # SQL Query
                if query['sql_query']:
                    st.markdown("**SQL Query:**")
                    st.code(query['sql_query'], language="sql")
                
                # Execution time
                if query['execution_time']:
                    st.caption(f"⏱️ Execution time: {query['execution_time']:.2f}s")
                
                # Visualization
                if query['figure_json']:
                    try:
                        fig = go.Figure(json.loads(query['figure_json']))
                        st.plotly_chart(fig, use_container_width=True)
                    except:
                        st.info("Visualization unavailable")
                
                # Feedback
                feedback_col1, feedback_col2, feedback_col3 = st.columns([1, 1, 10])
                with feedback_col1:
                    if st.button("👍", key=f"like_hist_{query['id']}"):
                        st.session_state.query_storage.update_feedback(query['id'], "like")
                        st.success("Feedback saved!")
                        st.rerun()
                with feedback_col2:
                    if st.button("👎", key=f"dislike_hist_{query['id']}"):
                        st.session_state.query_storage.update_feedback(query['id'], "dislike")
                        st.info("Feedback saved!")
                        st.rerun()
                
                # Save button
                if not query['is_saved']:
                    if st.button("💾 Save Query", key=f"save_hist_{query['id']}"):
                        st.session_state.query_storage.mark_as_saved(query['id'])
                        st.success("Query saved!")
                        st.rerun()
                else:
                    st.success("✅ Already saved")
                
                # Show current feedback
                if query['feedback'] != 'none':
                    feedback_emoji = '👍' if query['feedback'] == 'like' else '👎'
                    st.caption(f"Current feedback: {feedback_emoji}")

except Exception as e:
    st.error(f"Error loading history: {str(e)}")
