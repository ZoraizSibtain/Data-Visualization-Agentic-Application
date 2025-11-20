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

# Hide Streamlit navbar and footer
st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'query_history' not in st.session_state:
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
    "Best rated manufacturer": "Among all manufacturers, who has the best average review rating for their products?",
    "Top 5 best-selling products": "What are the top 5 best-selling products?",
}

GRAPH_SUGGESTIONS = {
    "Monthly revenue trends": "Plot a line chart of total monthly revenue to visualize sales trends over time.",
    "Delivery status distribution": "What is the percentage distribution of delivery statuses across all orders?",
    "Ratings by manufacturer": "Plot the average review rating per manufacturer to analyze product satisfaction by brand.",
    "Shipping cost by carrier": "Compare average shipping cost by carrier to evaluate cost efficiency.",
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
        st.markdown("### Table Queries")
        for name, query in TABLE_SUGGESTIONS.items():
            if st.button(name, key=f"sidebar_table_{name}", use_container_width=True):
                st.session_state.sidebar_query = query
                st.rerun()

        st.markdown("### Graph Queries")
        for name, query in GRAPH_SUGGESTIONS.items():
            if st.button(name, key=f"sidebar_graph_{name}", use_container_width=True):
                st.session_state.sidebar_query = query
                st.rerun()

        st.markdown("---")
        st.markdown("### Query History")
        if st.session_state.query_history:
            for i, item in enumerate(reversed(st.session_state.query_history[-10:])):
                query_preview = item['query'][:40] + '...' if len(item['query']) > 40 else item['query']
                if st.button(query_preview, key=f"history_{i}", use_container_width=True):
                    st.session_state.sidebar_query = item['query']
                    st.rerun()
        else:
            st.caption("No queries yet")

# ==================== ANALYTICS UI ====================
if st.session_state.ui_mode == 'analytics':
    import json
    import os
    from my_agent.metrics import metrics_tracker

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

    # Show test results and session analytics side by side if both available
    if test_results or analytics['total_queries'] > 0:
        main_cols = st.columns(2) if test_results and analytics['total_queries'] > 0 else [st.container()]

        # Test Suite Results
        if test_results:
            with main_cols[0] if analytics['total_queries'] > 0 else main_cols[0]:
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

                with st.expander("View Test Details"):
                    for q in test_results['queries']:
                        status_icon = "✅" if q['status'] == 'PASSED' else "⚠️" if q['status'] == 'NO DATA' else "❌"
                        st.text(f"{status_icon} {q['query'][:50]}... ({q['time']}s)")

        # Session Analytics
        if analytics['total_queries'] > 0:
            col_idx = 1 if test_results else 0
            with main_cols[col_idx] if test_results else main_cols[0]:
                st.markdown("## Session Analytics")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Queries", analytics['total_queries'])
                    st.metric("Avg Response Time", f"{analytics['avg_response_time']}s")
                with col2:
                    st.metric("Success Rate", f"{analytics['success_rate']}%")
                    st.metric("Under 5s", f"{analytics['queries_under_5s']}%")
    else:
        st.info("No queries processed yet. Run some queries to see analytics.")
        st.stop()

    if analytics['total_queries'] > 0:

        st.markdown("---")
        st.markdown("### Performance Breakdown")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Timing (avg)**")
            st.text(f"  SQL Generation: {analytics['avg_sql_gen_time']}s")
            st.text(f"  Query Execution: {analytics['avg_execution_time']}s")
            st.text(f"  Parsing: {analytics['avg_parse_time']}s")

        with col_b:
            st.markdown("**Chart Distribution**")
            for chart_type, count in analytics['chart_distribution'].items():
                st.text(f"  {chart_type}: {count}")

        if analytics['recent_queries']:
            st.markdown("---")
            st.markdown("### Recent Queries")
            for i, q in enumerate(reversed(analytics['recent_queries'][-5:])):
                status = "✅" if q['success'] else "❌"
                st.text(f"{status} {q['query']} ({q['time']}s)")

        # Show slow queries
        if analytics.get('slow_queries'):
            st.markdown("---")
            st.markdown("### Slow Queries (>5s)")
            for sq in reversed(analytics['slow_queries'][-5:]):
                st.warning(f"**{sq['time']}s** - {sq['query'][:60]}...")
                st.caption(f"SQL Gen: {sq['sql_gen_time']}s | Execution: {sq['execution_time']}s")

        # Show cache info
        st.markdown("---")
        st.caption(f"Cache size: {analytics.get('cache_size', 0)} queries cached")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Analytics"):
                metrics_tracker.save_to_file()
                st.success("Analytics saved to test_results.json")
        with col2:
            if st.button("Clear Analytics"):
                metrics_tracker.clear()
                st.rerun()

        # Performance improvement suggestions
        st.markdown("---")
        st.markdown("### Performance Suggestions")

        suggestions = []
        if analytics['avg_sql_gen_time'] > 2.0:
            suggestions.append("- **SQL Generation is slow** (>2s avg): Consider caching common query patterns or using a faster LLM model")
        if analytics['avg_execution_time'] > 1.0:
            suggestions.append("- **Query Execution is slow** (>1s avg): Add database indexes on frequently queried columns, or optimize JOIN operations")
        if analytics['queries_under_5s'] < 80:
            suggestions.append("- **Low percentage of fast queries** (<80% under 5s): Review slow queries in history for optimization opportunities")
        if analytics['success_rate'] < 95:
            suggestions.append("- **Success rate below 95%**: Check error patterns in recent queries to identify common failure modes")

        if suggestions:
            for s in suggestions:
                st.markdown(s)
        else:
            st.success("Performance looks good! All metrics within acceptable ranges.")

    st.stop()

# ==================== HISTORY UI ====================
if st.session_state.ui_mode == 'history':
    from my_agent.metrics import metrics_tracker

    queries = metrics_tracker.queries

    if not queries:
        st.info("No query history available. Run some queries to see them here.")
        st.stop()

    # Header row with refresh all button
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(f"**{len(queries)} queries** in history")
    with col2:
        refresh_all = st.button("Refresh All", type="primary", use_container_width=True)

    # Store selected query for rerun
    if 'rerun_query' not in st.session_state:
        st.session_state.rerun_query = None

    # Display queries in reverse chronological order
    for i, q in enumerate(reversed(queries)):
        idx = len(queries) - 1 - i

        with st.expander(
            f"**{q.query_text[:80]}{'...' if len(q.query_text) > 80 else ''}**",
            expanded=(st.session_state.rerun_query == idx)
        ):
            cols = st.columns([3, 1, 1, 1])

            with cols[0]:
                st.text_area("Full Query", value=q.query_text, disabled=True, height=80, key=f"query_{idx}")

            with cols[1]:
                st.metric("Total Time", f"{q.total_time:.2f}s")
                st.metric("Results", q.results_count)

            with cols[2]:
                st.metric("SQL Gen", f"{q.sql_gen_time:.2f}s")
                st.metric("Execution", f"{q.execution_time:.2f}s")

            with cols[3]:
                timestamp = q.timestamp.strftime("%Y-%m-%d %H:%M")
                st.caption(f"**Time:** {timestamp}")
                st.caption(f"**Chart:** {q.chart_type}")
                status = "✅ Success" if q.success else "❌ Failed"
                st.caption(f"**Status:** {status}")

            if q.sql_generated:
                st.code(q.sql_generated, language='sql')

            btn_cols = st.columns([1, 4])
            with btn_cols[0]:
                if st.button("🔄 Refresh", key=f"refresh_{idx}", use_container_width=True):
                    st.session_state.rerun_query = idx
                    st.rerun()

            if st.session_state.rerun_query == idx:
                with st.spinner("Re-running query..."):
                    processor = QueryProcessor()
                    result = processor.process_natural_language(q.query_text)
                    st.session_state.rerun_query = None

                if result['status'] == 'error':
                    st.error(result.get('message', 'Error running query'))
                elif result.get('data') is not None and not result['data'].empty:
                    data = result['data']
                    chart_type = result.get('chart_type', 'table')
                    if chart_type != 'table':
                        chart = ChartRenderer.render_chart(data, chart_type)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True, key=f"chart_{idx}")
                        else:
                            st.dataframe(data, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(data, use_container_width=True, hide_index=True)
                    st.success(f"Query refreshed with {len(data)} results")
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
                with st.container(border=True, height=400):
                    st.markdown("### Results")
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
                with st.container(border=True, height=400):
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

                with cols[0].container(border=True, height=400):
                    "### Visualization"
                    data = message["data"]

                    if current_chart != 'table':
                        chart = ChartRenderer.render_chart(data, current_chart)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True, key=f"plotly_{i}")
                        else:
                            st.dataframe(data, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(data, use_container_width=True, hide_index=True)

                with cols[1].container(border=True, height=400):
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
