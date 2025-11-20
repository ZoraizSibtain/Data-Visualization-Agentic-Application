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
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

def display_results():
    """Display results from session state with chart type switching."""
    if 'current_data' not in st.session_state or st.session_state.current_data is None:
        # Show a placeholder or welcome message if no data
        st.info("👋 Welcome! Ask a question below to generate analytics.")
        return

    data = st.session_state.current_data
    sql_query = st.session_state.get('current_sql', '')
    detected_type = st.session_state.get('detected_chart_type') or 'table'
    current_chart = st.session_state.get('current_chart_type', detected_type)
    
    # Create Tabs for Dashboard View
    tab_viz, tab_data, tab_sql = st.tabs(["📈 Visualization", "📋 Raw Data", "🔍 SQL Details"])

    with tab_viz:
        # Chart Controls
        col_ctrl, col_chart = st.columns([1, 4])
        
        with col_ctrl:
            st.subheader("Chart Settings")
            st.info(f"Detected: **{detected_type.upper()}**")
            
            st.markdown("### Change Type")
            chart_types = ['table', 'bar', 'line', 'pie', 'scatter']
            chart_labels = ['📋 Table', '📊 Bar', '📈 Line', '🥧 Pie', '⚡ Scatter']
            
            for ctype, label in zip(chart_types, chart_labels):
                if st.button(label, key=f"chart_btn_{ctype}", 
                           use_container_width=True,
                           type="primary" if current_chart == ctype else "secondary"):
                    st.session_state.current_chart_type = ctype
                    st.rerun()

        with col_chart:
            if current_chart != 'table':
                chart = ChartRenderer.render_chart(data, current_chart)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                else:
                    st.warning("Could not render this chart type with the current data.")
            else:
                st.dataframe(data, use_container_width=True)

    with tab_data:
        st.subheader("📋 Data Table")
        col_d1, col_d2 = st.columns([4, 1])
        with col_d1:
            st.dataframe(data, use_container_width=True, hide_index=True)
        with col_d2:
            csv = data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="query_results.csv",
                mime="text/csv",
                use_container_width=True
            )

    with tab_sql:
        st.subheader("Generated SQL")
        st.code(sql_query, language='sql')

def main():
    # Custom CSS for centering and scrolling
    st.markdown("""
        <style>
        .title-center {
            text-align: center;
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .subtitle-center {
            text-align: center;
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }
        .history-scroll {
            max-height: 70vh;
            overflow-y: auto;
            padding-right: 10px;
            border: 1px solid #f0f2f6;
            border-radius: 5px;
            padding: 10px;
        }
        /* Adjust main container to not be hidden by chat input */
        .block-container {
            padding-bottom: 100px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar with example queries and history
    with st.sidebar:
        st.header("📋 Example Queries")

        with st.expander("Tabular/Text Queries", expanded=True):
            example_queries_text = [
                "Which robot vacuum models have the highest number of delayed deliveries across all Chicago ZIP codes?",
                "Which warehouses are currently below their restock threshold based on stock level and capacity?",
                "Which Zip code has the highest number of delayed deliveries?",
                "Among all manufacturers, who has the best average review rating for their products?"
            ]
            for query in example_queries_text:
                if st.button(query[:40] + "...", key=f"text_{hash(query)}", help=query):
                    st.session_state.selected_query = query
                    st.session_state.auto_run = True
                    st.rerun()

        with st.expander("Chart Queries", expanded=True):
            example_queries_chart = [
                "Plot a line chart of total monthly revenue to visualize sales trends over time.",
                "What is the percentage distribution of delivery statuses across all orders?",
                "Plot the average review rating per manufacturer to analyze product satisfaction by brand.",
                "Compare average shipping cost by carrier to evaluate cost efficiency."
            ]
            for query in example_queries_chart:
                if st.button(query[:40] + "...", key=f"chart_{hash(query)}", help=query):
                    st.session_state.selected_query = query
                    st.session_state.auto_run = True
                    st.rerun()

        st.divider()
        
        # Query history in sidebar with custom scrolling
        with st.expander("📜 History", expanded=True):
            if st.session_state.query_history:
                # Use a container with max-height for scrolling
                with st.container(height=400):
                    for i, item in enumerate(reversed(st.session_state.query_history)):
                        # Display just the prompt as a button
                        if st.button(f"{item['query']}", key=f"hist_{len(st.session_state.query_history)-i}", help=f"Type: {item['chart_type']}"):
                            st.session_state.selected_query = item['query']
                            st.session_state.auto_run = True
                            st.rerun()
            else:
                st.caption("No history yet.")

        st.divider()
        if st.button("🗑️ Clear Results", use_container_width=True):
            # Clear stored results
            for key in ['current_data', 'current_sql', 'current_chart_type', 'detected_chart_type']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # --- MAIN CONTENT AREA ---

    # 1. Title (Top, Centered)
    st.markdown('<div class="title-center">🤖 Robot Vacuum Depot Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-center">Natural Language Data Visualization</div>', unsafe_allow_html=True)

    # 2. Dashboard (Middle)
    # Use a container with a fixed height to keep the input box relatively stable
    with st.container(height=600, border=True):
        display_results()

    # 3. Chat Input (Bottom)
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("💬 Ask a Question")
        
        # Handle inputs from Sidebar (History or Examples)
        if 'selected_query' in st.session_state:
            st.session_state.input_area = st.session_state.pop('selected_query')
            # If we want to auto-run, we can check a flag, but user asked to "show in text box"
            # We will respect the "show" requirement. If auto_run is set, we can trigger it.
        
        user_input = st.text_area(
            "Enter your query:",
            height=70,
            placeholder="e.g., What is the average review rating per manufacturer?",
            key="input_area",
            label_visibility="collapsed"
        )

        col1, col2 = st.columns([1, 6])
        with col1:
            analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
        with col2:
            if st.button("🗑️ Clear Results", use_container_width=False):
                 # Clear stored results
                for key in ['current_data', 'current_sql', 'current_chart_type', 'detected_chart_type']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    # Check for auto-run
    auto_run = st.session_state.pop('auto_run', False)

    if (analyze_button or auto_run) and user_input:
        if len(user_input) < 10:
            st.error("Query too short. Please enter at least 10 characters.")
        else:
            with st.spinner("Processing your query..."):
                try:
                    processor = QueryProcessor()
                    result = processor.process_natural_language(user_input)

                    if result['status'] == 'error':
                        st.error(f"Error: {result.get('message', 'Unknown error')}")
                        with st.expander("View Generated SQL"):
                            st.code(result.get('sql_query', 'N/A'), language='sql')
                    else:
                        if result['data'] is not None and not result['data'].empty:
                            st.session_state.current_data = result['data']
                            st.session_state.current_sql = result['sql_query']
                            st.session_state.current_chart_type = result['chart_type']
                            st.session_state.detected_chart_type = result['chart_type']

                            # Add to history (avoid duplicates if clicking history)
                            # We'll add it if it's not the exact same as the last one
                            if not st.session_state.query_history or st.session_state.query_history[-1]['query'] != user_input:
                                st.session_state.query_history.append({
                                    'query': user_input,
                                    'chart_type': result['chart_type']
                                })
                            
                            st.rerun()
                        else:
                            st.warning("No data found for this query.")

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.exception(e)

if __name__ == "__main__":
    main()
