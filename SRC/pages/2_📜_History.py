import streamlit as st
import plotly.io as pio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.query_storage import QueryStorage
from config import DATABASE_URL
from utils.sidebar import render_sidebar

st.set_page_config(
    page_title="History - Agentic Data Analysis",
    page_icon="📜",
    layout="wide"
)

# Custom CSS for card layout
st.markdown("""
<style>
    .query-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #3d3d5c;
        height: 100%;
    }
    .query-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }
    .card-timestamp {
        color: #888;
        font-size: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .card-question {
        color: #fff;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-badges {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .card-badge {
        background: rgba(102, 126, 234, 0.2);
        color: #667eea;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
    }
    .card-badge-saved {
        background: rgba(0, 204, 150, 0.2);
        color: #00CC96;
    }
    .card-badge-like {
        background: rgba(0, 204, 150, 0.2);
        color: #00CC96;
    }
    .card-badge-dislike {
        background: rgba(239, 85, 59, 0.2);
        color: #EF553B;
    }
</style>
""", unsafe_allow_html=True)

# Render shared sidebar
render_sidebar()

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
        options=[12, 24, 48, 100],
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

    # Create 4-column grid
    for row_start in range(0, len(queries), 4):
        cols = st.columns(4)
        for col_idx, query_idx in enumerate(range(row_start, min(row_start + 4, len(queries)))):
            query = queries[query_idx]
            with cols[col_idx]:
                timestamp = query['timestamp'].strftime('%Y-%m-%d %H:%M') if query['timestamp'] else 'Unknown'

                # Build badges
                badges_html = ""
                if query['is_saved']:
                    badges_html += '<span class="card-badge card-badge-saved">💾 Saved</span>'
                if query['feedback'] == 'like':
                    badges_html += '<span class="card-badge card-badge-like">👍</span>'
                elif query['feedback'] == 'dislike':
                    badges_html += '<span class="card-badge card-badge-dislike">👎</span>'
                if query['figure_json']:
                    badges_html += '<span class="card-badge">📊 Chart</span>'
                if query['execution_time']:
                    badges_html += f'<span class="card-badge">{query["execution_time"]:.1f}s</span>'

                # Truncate question
                question_preview = query['user_question'][:100] + ('...' if len(query['user_question']) > 100 else '')

                st.markdown(f"""
                <div class="query-card">
                    <div class="card-timestamp">{timestamp}</div>
                    <div class="card-question">{question_preview}</div>
                    <div class="card-badges">{badges_html}</div>
                </div>
                """, unsafe_allow_html=True)

                # Action buttons
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("👁️ View", key=f"view_{query_idx}", use_container_width=True):
                        st.session_state[f"expanded_{query_idx}"] = True
                with col_b:
                    if st.button("🗑️", key=f"del_{query_idx}", use_container_width=True):
                        query_storage.delete_query(query['id'])
                        st.rerun()

    st.markdown("---")

    # Show expanded query details in modal-like section
    for i, query in enumerate(queries):
        if st.session_state.get(f"expanded_{i}", False):
            st.markdown(f"### Query Details")

            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("✕ Close", key=f"close_{i}"):
                    st.session_state[f"expanded_{i}"] = False
                    st.rerun()

            timestamp = query['timestamp'].strftime('%Y-%m-%d %H:%M') if query['timestamp'] else 'Unknown'
            st.caption(f"Time: {timestamp}")

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

            # SQL and Python in tabs
            if query['sql_query'] or query['python_code']:
                tab1, tab2 = st.tabs(["SQL Query", "Python Code"])
                with tab1:
                    if query['sql_query']:
                        st.code(query['sql_query'], language='sql')
                with tab2:
                    if query['python_code']:
                        st.code(query['python_code'], language='python')

            # Metadata and Actions
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if query['execution_time']:
                    st.metric("Execution Time", f"{query['execution_time']:.2f}s")
            with col2:
                st.metric("Feedback", query['feedback'].capitalize())
            with col3:
                if not query['is_saved']:
                    if st.button("💾 Save Query", key=f"save_hist_{i}"):
                        query_storage.mark_as_saved(query['id'], True)
                        st.success("Saved!")
                        st.rerun()
                else:
                    st.success("✓ Saved")

            st.markdown("---")
            break  # Only show one expanded at a time
