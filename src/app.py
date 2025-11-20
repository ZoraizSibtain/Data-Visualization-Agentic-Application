import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from agentic_processor.query_processor import QueryProcessor
from visualization.chart_renderer import ChartRenderer

# Page configuration
st.set_page_config(
    page_title="Robot Vacuum Depot Analytics",
    page_icon="🤖",
    layout="wide",
)

# Hide Streamlit navbar and footer, make header sticky
from assets.styles import CUSTOM_CSS

# Hide Streamlit navbar and footer, make header sticky
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize session state
if 'query_history' not in st.session_state:
    # Load history from metrics tracker
    from my_agent.metrics import metrics_tracker
    st.session_state.query_history = [
        {'query': q.query_text, 'chart_type': q.chart_type} 
        for q in metrics_tracker.queries
    ]
    if not st.session_state.query_history:
        st.session_state.query_history = []
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'ui_mode' not in st.session_state:
    st.session_state.ui_mode = 'chat'
if 'dashboard_query' not in st.session_state:
    st.session_state.dashboard_query = None
if 'dashboard_result' not in st.session_state:
    st.session_state.dashboard_result = None
if 'sidebar_query' not in st.session_state:
    st.session_state.sidebar_query = None

# Example suggestions - split into tabular and graph
TABLE_SUGGESTIONS = {
    "Delayed deliveries by model": "Which robot vacuum models have the highest number of delayed deliveries across all Chicago ZIP codes?",
    "Warehouses below threshold": "Which warehouses are currently below their restock threshold based on stock level and capacity?",
    "Zip code with most delays": "Which Zip code has the highest number of delayed deliveries?",
    "Best rated manufacturer": "Among all manufacturers, who has the best average review rating for their products?",
}

GRAPH_SUGGESTIONS = {
    "Monthly revenue trend": "Plot a line chart of total monthly revenue to visualize sales trends over time.",
    "Delivery status distribution": "What is the percentage distribution of delivery statuses (Delivered, Delayed, Canceled, Fraud, etc.) across all orders?",
    "Ratings by manufacturer": "Plot the average review rating per manufacturer to analyze product satisfaction by brand.",
    "Shipping cost by Carrier": "Compare average shipping cost by carrier to evaluate cost efficiency.",
}

# Combined for backwards compatibility
SUGGESTIONS = {**TABLE_SUGGESTIONS, **GRAPH_SUGGESTIONS}

# Title row with mode switcher
title_row = st.columns([6, 1, 1])

with title_row[0]:
    st.title("🤖 Robot Vacuum Depot Analytics", anchor=False)

with title_row[1]:
    ui_modes = ['Chat', 'Dashboard', 'Analytics', 'History']
    mode_map = {'chat': 0, 'dashboard': 1, 'analytics': 2, 'history': 3}
    current_mode_idx = mode_map.get(st.session_state.ui_mode, 0)
    selected_mode = st.selectbox(
        "UI Mode",
        ui_modes,
        index=current_mode_idx,
        label_visibility="collapsed"
    )
    new_mode = selected_mode.lower()
    if new_mode != st.session_state.ui_mode:
        st.session_state.ui_mode = new_mode
        st.rerun()

# Shared sidebar for all modes (except analytics)
if st.session_state.ui_mode in ['chat', 'dashboard']:
    with st.sidebar:
        st.markdown("### 🟢 System Status")
        st.caption("Database: **Connected**")
        st.caption("Agent: **Active**")
        st.markdown("---")

        st.markdown("### 📝 Sample Queries")
        
        with st.expander("📊 Tables", expanded=True):
            for name, query in TABLE_SUGGESTIONS.items():
                if st.button(name, key=f"sidebar_table_{name}", use_container_width=True):
                    st.session_state.sidebar_query = query
                    st.rerun()

        with st.expander("📈 Charts", expanded=True):
            for name, query in GRAPH_SUGGESTIONS.items():
                if st.button(name, key=f"sidebar_graph_{name}", use_container_width=True):
                    st.session_state.sidebar_query = query
                    st.rerun()

        st.markdown("---")
        st.markdown("### 🕒 Recent History")
        if st.session_state.query_history:
            for i, item in enumerate(reversed(st.session_state.query_history[-5:])):
                query_preview = item['query'][:35] + '...' if len(item['query']) > 35 else item['query']
                if st.button(f"↺ {query_preview}", key=f"history_{i}", use_container_width=True, help=item['query']):
                    st.session_state.sidebar_query = item['query']
                    st.rerun()
        else:
            st.caption("No queries yet")

# ==================== ANALYTICS UI ====================
if st.session_state.ui_mode == 'analytics':
    import json
    import os
    from my_agent.metrics import metrics_tracker

    # Add Save/Clear buttons to title row
    with title_row[2]:
        ac1, ac2 = st.columns(2)
        with ac1:
            if st.button("💾", help="Save Analytics", use_container_width=True):
                metrics_tracker.save_to_file()
                st.toast("Analytics saved to test_results.json")
        with ac2:
            if st.button("🗑️", help="Clear Analytics", use_container_width=True):
                metrics_tracker.clear()
                st.rerun()

    analytics = metrics_tracker.get_analytics()

    # Load test results if available
    test_results = None
    test_results_file = 'test_results.json'
    if os.path.exists(test_results_file):
        try:
            with open(test_results_file, 'r') as f:
                test_results = json.load(f)
        except Exception:
            pass

    # Show session analytics and test results side by side
    if test_results or analytics['total_queries'] > 0:
        main_cols = st.columns(2) if test_results and analytics['total_queries'] > 0 else [st.container()]

        # Session Analytics (LEFT)
        if analytics['total_queries'] > 0:
            with main_cols[0]:
                st.markdown("## Session Analytics")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Queries", analytics['total_queries'])
                    st.metric("Avg Response Time", f"{analytics['avg_response_time']}s")
                with col2:
                    st.metric("Success Rate", f"{analytics['success_rate']}%")
                    st.metric("Under 5s", f"{analytics['queries_under_5s']}%")

        # Test Suite Results (RIGHT)
        if test_results:
            col_idx = 1 if analytics['total_queries'] > 0 else 0
            with main_cols[col_idx] if analytics['total_queries'] > 0 else main_cols[0]:
                st.markdown("## Test Suite Results")
                summary = test_results['summary']

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tests Run", summary['total_tests'])
                    st.metric("Passed", summary['passed'])
                with col2:
                    st.metric("Avg Time", f"{summary['avg_time']}s")
                    st.metric("Under 5s", f"{summary['under_5s_percent']}%")

                st.caption(f"Last run: {test_results['timestamp'][:19]}")
    else:
        st.info("No queries processed yet. Run some queries to see analytics.")
        st.stop()

    if analytics['total_queries'] > 0:

        st.markdown("---")

        # Performance Breakdown (LEFT) and Cache Stats (RIGHT)
        perf_cols = st.columns(2)

        with perf_cols[0]:
            st.markdown("### Performance Breakdown")

            st.markdown("**Timing (average)**")
            timing_cols = st.columns(3)
            with timing_cols[0]:
                st.metric("SQL Gen", f"{analytics['avg_sql_gen_time']}s")
            with timing_cols[1]:
                st.metric("Execution", f"{analytics['avg_execution_time']}s")
            with timing_cols[2]:
                st.metric("Parsing", f"{analytics['avg_parse_time']}s")

            st.markdown("**Chart Distribution**")
            chart_types = list(analytics['chart_distribution'].keys())
            chart_counts = list(analytics['chart_distribution'].values())
            if chart_types:
                chart_cols = st.columns(len(chart_types))
                for i, (chart_type, count) in enumerate(zip(chart_types, chart_counts)):
                    with chart_cols[i]:
                        st.metric(chart_type.title(), count)

        with perf_cols[1]:
            st.markdown("### Cache Performance")
            st.markdown(f"**Cache Size: {analytics.get('cache_size', 0)} queries cached**")

            cache_cols = st.columns(2)
            with cache_cols[0]:
                st.metric("Cached Queries", analytics.get('cached_queries', 0))
                st.metric("Avg Cached Time", f"{analytics.get('avg_cached_time', 0)}s")
            with cache_cols[1]:
                st.metric("Non-cached Queries", analytics.get('non_cached_queries', 0))
                st.metric("Avg Non-cached Time", f"{analytics.get('avg_non_cached_time', 0)}s")

        st.markdown("---")

        # Slow Queries (Full Width, 2 Columns)
        st.markdown("### Slow Queries (>5s)")
        
        if analytics.get('slow_queries'):
            slow_queries = list(reversed(analytics['slow_queries'][-10:]))
            sq_cols = st.columns(2)
            
            for i, sq in enumerate(slow_queries):
                col_idx = i % 2
                with sq_cols[col_idx]:
                    with st.container(border=True):
                        st.warning(f"**{sq['time']}s** - {sq['query']}")
                        st.caption(f"SQL Gen: {sq['sql_gen_time']}s | Execution: {sq['execution_time']}s")
        else:
            st.success("No slow queries! All queries under 5s.")

    st.stop()

# ==================== HISTORY UI ====================
if st.session_state.ui_mode == 'history':
    from my_agent.metrics import metrics_tracker

    # Add Refresh All button to title row
    with title_row[2]:
        refresh_all = st.button("Refresh All", type="primary", use_container_width=True)

    queries = metrics_tracker.queries

    if not queries:
        st.info("No query history available. Run some queries to see them here.")
        st.stop()

    # Show query count
    st.markdown(f"**{len(queries)} queries** in history")

    # Store selected query for rerun
    if 'rerun_query' not in st.session_state:
        st.session_state.rerun_query = None

    # Display queries in grid layout
    NUM_COLS = 3
    cols = st.columns(NUM_COLS)

    for i, q in enumerate(reversed(queries)):
        idx = len(queries) - 1 - i
        col_idx = i % NUM_COLS
        
        with cols[col_idx].container(border=True):
            # Card Header: Query Text (Full Title)
            st.markdown(f"**{q.query_text}**")
            st.markdown("---")
            
            # Chart Area
            if hasattr(q, 'result_data') and q.result_data:
                try:
                    df = pd.DataFrame(q.result_data)
                    if not df.empty and q.chart_type != 'table':
                        chart = ChartRenderer.render_chart(df, q.chart_type)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True, key=f"hist_chart_{idx}")
                        else:
                            st.dataframe(df.head(5), use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(df.head(5), use_container_width=True, hide_index=True)
                except Exception as e:
                    st.caption(f"Could not render chart: {str(e)}")
            else:
                st.info("No data available for preview", icon="ℹ️")

            # Metrics Row
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.caption(f"⏱️ {q.total_time:.2f}s")
            with m_col2:
                st.caption(f"📊 {q.chart_type}")
            
            # Status & Timestamp
            status_icon = "✅" if q.success else "❌"
            timestamp = q.timestamp.strftime("%H:%M %d/%m")
            st.caption(f"{status_icon} {timestamp}")
            
            # Actions
            if st.button("🔄 Rerun", key=f"rerun_{idx}", use_container_width=True):
                st.session_state.rerun_query = idx
                st.rerun()

            # View Details Expander
            with st.expander("Details"):
                st.text_area("SQL", value=q.sql_generated, height=150, disabled=True, key=f"sql_{idx}")
                detail_cols = st.columns(2)
                with detail_cols[0]:
                    st.metric("Rows", q.results_count)
                with detail_cols[1]:
                    st.metric("SQL Gen", f"{q.sql_gen_time:.2f}s")

    # Handle Rerun Logic (outside loop)
    if st.session_state.rerun_query is not None:
        idx = st.session_state.rerun_query
        q = queries[idx]
        
        with st.spinner(f"Re-running: {q.query_text[:30]}..."):
            processor = QueryProcessor()
            result = processor.process_natural_language(q.query_text)
            st.session_state.rerun_query = None

        if result['status'] == 'error':
            st.error(result.get('message', 'Error running query'))
        elif result.get('data') is not None and not result['data'].empty:
            data = result['data']
            chart_type = result.get('chart_type', 'table')
            
            # Show result in a modal-like container at the top
            st.markdown("### 🔄 Rerun Results")
            st.info(f"Query: {q.query_text}")
            
            if chart_type != 'table':
                chart = ChartRenderer.render_chart(data, chart_type)
                if chart:
                    st.plotly_chart(chart, use_container_width=True, key=f"rerun_chart_{idx}")
                else:
                    st.dataframe(data, use_container_width=True, hide_index=True)
            else:
                st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.warning(result.get('message', 'No results returned'))

    if refresh_all:
        progress = st.progress(0, "Refreshing all queries...")
        processor = QueryProcessor()
        for i, q in enumerate(queries):
            progress.progress((i + 1) / len(queries), f"Refreshing query {i + 1}/{len(queries)}...")
            try:
                processor.process_natural_language(q.query_text)
            except Exception as e:
                st.error(f"Failed to refresh query '{q.query_text[:50]}...': {str(e)}")
        progress.empty()
        st.success(f"Refreshed {len(queries)} queries!")
        st.rerun()

    st.stop()

# ==================== DASHBOARD UI ====================
if st.session_state.ui_mode == 'dashboard':
    with title_row[2]:
        def clear_dashboard():
            st.session_state.dashboard_query = None
            st.session_state.dashboard_result = None
            st.session_state.sidebar_query = None
            if 'dashboard_chart_type' in st.session_state:
                del st.session_state['dashboard_chart_type']
        st.button("Clear", icon=":material/refresh:", on_click=clear_dashboard)

    # Check for sidebar query to auto-run
    auto_run_query = None
    if st.session_state.sidebar_query:
        auto_run_query = st.session_state.sidebar_query
        st.session_state.sidebar_query = None

    # Process auto-run query
    if auto_run_query:
        with st.spinner("Processing query..."):
            try:
                processor = QueryProcessor()
                result = processor.process_natural_language(auto_run_query)
                st.session_state.dashboard_query = auto_run_query
                st.session_state.dashboard_result = result

                # Add to query history
                if result.get('data') is not None:
                    if not st.session_state.query_history or st.session_state.query_history[-1]['query'] != auto_run_query:
                        st.session_state.query_history.append({
                            'query': auto_run_query,
                            'chart_type': result.get('chart_type', 'table')
                        })
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Display results first (before input)
    if st.session_state.dashboard_result:
        result = st.session_state.dashboard_result

        # Show current query
        if st.session_state.dashboard_query:
            st.caption(f"**Query:** {st.session_state.dashboard_query}")

        if result['status'] == 'error':
            st.error(result.get('message', 'Unknown error'))
        elif result.get('data') is not None and not result['data'].empty:
            data = result['data']

            # Chart type selector
            chart_types = ['table', 'bar', 'line', 'pie', 'scatter']
            if 'dashboard_chart_type' not in st.session_state:
                st.session_state.dashboard_chart_type = result.get('chart_type', 'table')

            selected_chart = st.pills(
                "Visualization",
                chart_types,
                default=st.session_state.dashboard_chart_type,
                key="dashboard_chart_pills"
            )
            if selected_chart:
                st.session_state.dashboard_chart_type = selected_chart

            # Results layout
            cols = st.columns([3, 1])

            with cols[0]:
                with st.container(border=True, height=500):
                    # st.markdown("### Results")
                    chart_type = st.session_state.dashboard_chart_type

                    if chart_type != 'table':
                        chart = ChartRenderer.render_chart(data, chart_type)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True, key="dashboard_plotly")
                        else:
                            st.dataframe(data, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(data, use_container_width=True, hide_index=True)

            with cols[1]:
                with st.container(border=True, height=500):
                    st.markdown("### Summary")
                    st.metric("Rows", len(data))
                    st.metric("Columns", len(data.columns))

                    csv = data.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        data=csv,
                        file_name="results.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="dashboard_download"
                    )

            # SQL details (expanded by default)
            with st.expander("Generated SQL", expanded=True):
                st.code(result.get('sql_query', ''), language='sql')
        else:
            st.warning(result.get('message', 'No data found.'))

    # Input at bottom (like chat UI)
    dashboard_input = st.chat_input("Ask a question about your robot vacuum data...")

    if dashboard_input:
        with st.spinner("Processing query..."):
            try:
                processor = QueryProcessor()
                result = processor.process_natural_language(dashboard_input)
                st.session_state.dashboard_query = dashboard_input
                st.session_state.dashboard_result = result

                # Add to query history
                if result.get('data') is not None:
                    if not st.session_state.query_history or st.session_state.query_history[-1]['query'] != dashboard_input:
                        st.session_state.query_history.append({
                            'query': dashboard_input,
                            'chart_type': result.get('chart_type', 'table')
                        })
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.stop()

# ==================== CHAT UI ====================
with title_row[2]:
    def clear_conversation():
        st.session_state.messages = []
        st.session_state.initial_question = None
        st.session_state.selected_suggestion = None
        for key in ['current_data', 'current_sql', 'current_chart_type', 'detected_chart_type']:
            if key in st.session_state:
                del st.session_state[key]
    st.button("Restart", icon=":material/refresh:", on_click=clear_conversation)

# Check if user just submitted initial question or clicked suggestion
user_just_asked_initial_question = (
    "initial_question" in st.session_state and st.session_state.initial_question
)

user_just_clicked_suggestion = (
    "selected_suggestion" in st.session_state and st.session_state.selected_suggestion
)

user_first_interaction = (
    user_just_asked_initial_question or user_just_clicked_suggestion
)

has_message_history = len(st.session_state.messages) > 0

# Chat input always at bottom
user_message = st.chat_input("Ask a question about your robot vacuum data...")

# Handle sidebar query click
if not user_message and st.session_state.sidebar_query:
    user_message = st.session_state.sidebar_query
    st.session_state.sidebar_query = None

# Handle initial question from session state
if not user_message and user_just_asked_initial_question:
    user_message = st.session_state.initial_question
    st.session_state.initial_question = None

if not user_message and user_just_clicked_suggestion:
    user_message = SUGGESTIONS[st.session_state.selected_suggestion]
    st.session_state.selected_suggestion = None

# Display chat messages from history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.container()  # Fix ghost message bug

        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            # For assistant messages, show the visualization if available
            if "data" in message and message["data"] is not None:
                # Show chart type selector
                chart_types = ['table', 'bar', 'line', 'pie', 'scatter']
                current_chart = message.get("chart_type", "table")

                selected_chart = st.pills(
                    "Chart type",
                    chart_types,
                    default=current_chart,
                    selection_mode="single",
                    key=f"chart_pills_{i}"
                )

                if selected_chart and selected_chart != current_chart:
                    st.session_state.messages[i]["chart_type"] = selected_chart
                    st.rerun()

                ""

                # Main visualization and data layout
                cols = st.columns([3, 1])

                with cols[0].container(border=True, height=500):
                    # "### Visualization"
                    data = message["data"]

                    if current_chart != 'table':
                        chart = ChartRenderer.render_chart(data, current_chart)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True, key=f"plotly_{i}")
                        else:
                            st.dataframe(data, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(data, use_container_width=True, hide_index=True)

                with cols[1].container(border=True, height=500):
                    "### Summary"
                    st.metric("Total Rows", len(data))
                    st.metric("Columns", len(data.columns))

                    ""

                    csv = data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key=f"download_{i}"
                    )

                # SQL Details
                with st.expander("🔍 Generated SQL"):
                    st.code(message.get("sql_query", ""), language='sql')

            else:
                st.markdown(message["content"])

# Process new user message
if user_message:
    # Display user message
    with st.chat_message("user"):
        st.text(user_message)

    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your question..."):
            try:
                processor = QueryProcessor()
                result = processor.process_natural_language(user_message)

                if result['status'] == 'error':
                    response_content = f"Error: {result.get('message', 'Unknown error')}"
                    st.error(response_content)

                    # Add to history
                    st.session_state.messages.append({"role": "user", "content": user_message})
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_content,
                        "data": None
                    })

                else:
                    if result['data'] is not None and not result['data'].empty:
                        # Store in session state
                        st.session_state.current_data = result['data']
                        st.session_state.current_sql = result['sql_query']
                        st.session_state.current_chart_type = result['chart_type']

                        # Add to history
                        st.session_state.messages.append({"role": "user", "content": user_message})
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Found {len(result['data'])} results",
                            "data": result['data'],
                            "sql_query": result['sql_query'],
                            "chart_type": result['chart_type']
                        })

                        # Add to query history
                        if not st.session_state.query_history or st.session_state.query_history[-1]['query'] != user_message:
                            st.session_state.query_history.append({
                                'query': user_message,
                                'chart_type': result['chart_type']
                            })

                        st.rerun()
                    else:
                        message = result.get('message', 'No data found for this query.')
                        st.warning(message)

                        # Add to history
                        st.session_state.messages.append({"role": "user", "content": user_message})
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": message,
                            "data": None
                        })

            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                st.error(error_msg)
                st.exception(e)

                # Add to history
                st.session_state.messages.append({"role": "user", "content": user_message})
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "data": None
                })
