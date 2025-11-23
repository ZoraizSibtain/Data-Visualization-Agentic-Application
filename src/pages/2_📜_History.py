import streamlit as st
import plotly.io as pio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.query_storage import QueryStorage
from config import DATABASE_URL

st.set_page_config(
    page_title="History - Agentic Data Analysis",
    page_icon="📜",
    layout="wide"
)

st.title("📜 Query History")

# Initialize query storage
if 'query_storage' not in st.session_state or st.session_state.query_storage is None:
    try:
        st.session_state.query_storage = QueryStorage(DATABASE_URL)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.stop()

query_storage = st.session_state.query_storage

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    search = st.text_input("🔍 Search queries", placeholder="Enter keywords...")

with col2:
    time_range = st.selectbox(
        "⏰ Time range",
        options=['all', '24h', '7d', '30d'],
        format_func=lambda x: {
            'all': 'All time',
            '24h': 'Last 24 hours',
            '7d': 'Last 7 days',
            '30d': 'Last 30 days'
        }.get(x, x)
    )

with col3:
    limit = st.selectbox(
        "📊 Show",
        options=[10, 25, 50, 100],
        format_func=lambda x: f"{x} queries"
    )

st.markdown("---")

# Get queries
queries = query_storage.get_all_queries(
    search=search if search else None,
    time_range=time_range if time_range != 'all' else None,
    limit=limit
)

if not queries:
    st.info("No queries found. Start chatting to build your history!")
else:
    st.markdown(f"**Found {len(queries)} queries**")

    for i, query in enumerate(queries):
        timestamp = query['timestamp'].strftime('%Y-%m-%d %H:%M') if query['timestamp'] else 'Unknown'
        feedback_emoji = ""
        if query['feedback'] == 'like':
            feedback_emoji = "👍 "
        elif query['feedback'] == 'dislike':
            feedback_emoji = "👎 "

        saved_emoji = "💾 " if query['is_saved'] else ""

        with st.expander(f"{saved_emoji}{feedback_emoji}{timestamp} - {query['user_question'][:100]}"):
            # Question
            st.markdown(f"**Question:** {query['user_question']}")

            # Visualization
            if query['figure_json']:
                try:
                    fig = pio.from_json(query['figure_json'])
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not load visualization: {e}")

            # Result
            if query['result_text']:
                st.markdown("**Result:**")
                st.text(query['result_text'][:500])

            # SQL
            if query['sql_query']:
                st.markdown("**SQL Query:**")
                st.code(query['sql_query'], language='sql')

            # Python code
            if query['python_code']:
                st.markdown("**Python Code:**")
                st.code(query['python_code'], language='python')

            # Metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                if query['execution_time']:
                    st.metric("Execution Time", f"{query['execution_time']:.2f}s")
            with col2:
                st.metric("Feedback", query['feedback'].capitalize())
            with col3:
                st.metric("Saved", "Yes" if query['is_saved'] else "No")

            # Actions
            col1, col2 = st.columns(2)
            with col1:
                if not query['is_saved']:
                    if st.button("💾 Save Query", key=f"save_hist_{i}"):
                        query_storage.mark_as_saved(query['id'], True)
                        st.success("Saved!")
                        st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"delete_hist_{i}"):
                    query_storage.delete_query(query['id'])
                    st.rerun()
