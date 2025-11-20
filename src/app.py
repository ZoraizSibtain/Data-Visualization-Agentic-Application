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
    layout="wide"
)

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

def display_results():
    """Display results from session state with chart type switching."""
    if 'current_data' not in st.session_state or st.session_state.current_data is None:
        return

    data = st.session_state.current_data
    sql_query = st.session_state.get('current_sql', '')
    detected_type = st.session_state.get('detected_chart_type') or 'table'

    # Show SQL query
    with st.expander("View Generated SQL", expanded=False):
        st.code(sql_query, language='sql')

    # Show chart type detected
    st.info(f"📊 Chart Type Detected: **{detected_type.upper()}**")

    # Chart type selection buttons
    st.subheader("📊 Visualization Options")
    chart_cols = st.columns(5)
    chart_types = ['table', 'bar', 'line', 'pie', 'scatter']
    chart_labels = ['📋 Table', '📊 Bar', '📈 Line', '🥧 Pie', '⚡ Scatter']

    current_chart = st.session_state.get('current_chart_type', detected_type)

    for i, (ctype, label) in enumerate(zip(chart_types, chart_labels)):
        with chart_cols[i]:
            if st.button(label, key=f"chart_btn_{ctype}",
                       type="primary" if current_chart == ctype else "secondary"):
                st.session_state.current_chart_type = ctype
                st.rerun()

    # Get current chart type
    display_chart_type = st.session_state.get('current_chart_type', detected_type)

    # Chart visualization
    if display_chart_type != 'table':
        chart = ChartRenderer.render_chart(data, display_chart_type)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("Could not render this chart type with the current data.")

    # Always show data table
    st.subheader("📋 Data Table")
    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True
    )

    # Download option
    csv = data.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="query_results.csv",
        mime="text/csv"
    )

def main():
    st.title("🤖 Robot Vacuum Depot Analytics")
    st.markdown("### Natural Language Data Visualization")

    # Sidebar with example queries
    with st.sidebar:
        st.header("📋 Example Queries")

        st.subheader("Tabular/Text Queries")
        example_queries_text = [
            "Which robot vacuum models have the highest number of delayed deliveries across all Chicago ZIP codes?",
            "Which warehouses are currently below their restock threshold based on stock level and capacity?",
            "Which Zip code has the highest number of delayed deliveries?",
            "Among all manufacturers, who has the best average review rating for their products?"
        ]

        for query in example_queries_text:
            if st.button(query[:50] + "...", key=f"text_{hash(query)}"):
                st.session_state.selected_query = query
                st.session_state.auto_run = True
                st.rerun()

        st.subheader("Chart Queries")
        example_queries_chart = [
            "Plot a line chart of total monthly revenue to visualize sales trends over time.",
            "What is the percentage distribution of delivery statuses across all orders?",
            "Plot the average review rating per manufacturer to analyze product satisfaction by brand.",
            "Compare average shipping cost by carrier to evaluate cost efficiency."
        ]

        for query in example_queries_chart:
            if st.button(query[:50] + "...", key=f"chart_{hash(query)}"):
                st.session_state.selected_query = query
                st.session_state.auto_run = True
                st.rerun()

        st.markdown("---")
        st.markdown("**Instructions:**")
        st.markdown("1. Enter a natural language query")
        st.markdown("2. Click 'Analyze' to process")
        st.markdown("3. View results as table or chart")

    # Main input area
    # Update input text if an example query was selected
    if 'selected_query' in st.session_state:
        st.session_state.input_area = st.session_state.pop('selected_query')

    user_input = st.text_area(
        "Enter your query in natural language:",
        height=100,
        max_chars=500,
        placeholder="e.g., What is the average review rating per manufacturer?",
        key="input_area"
    )


    col1, col2 = st.columns([1, 5])
    with col1:
        analyze_button = st.button("🔍 Analyze", type="primary")
    with col2:
        if st.button("🗑️ Clear"):
            # Clear stored results
            for key in ['current_data', 'current_sql', 'current_chart_type', 'detected_chart_type']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # Check for auto-run from example query
    auto_run = st.session_state.pop('auto_run', False)

    # Process query
    if (analyze_button or auto_run) and user_input:
        if len(user_input) < 10:
            st.error("Query too short. Please enter at least 10 characters.")
            return

        with st.spinner("Processing your query..."):
            try:
                processor = QueryProcessor()
                result = processor.process_natural_language(user_input)

                # Display results
                if result['status'] == 'error':
                    st.error(f"Error: {result.get('message', 'Unknown error')}")
                    with st.expander("View Generated SQL"):
                        st.code(result.get('sql_query', 'N/A'), language='sql')
                else:
                    if result['data'] is not None and not result['data'].empty:
                        # Store result in session state
                        st.session_state.current_data = result['data']
                        st.session_state.current_sql = result['sql_query']
                        st.session_state.current_chart_type = result['chart_type']
                        st.session_state.detected_chart_type = result['chart_type']

                        # Add to history
                        st.session_state.query_history.append({
                            'query': user_input,
                            'chart_type': result['chart_type']
                        })
                    else:
                        st.warning("No data found for this query.")
                        return

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)
                return

    # Display results (either new or from session state)
    display_results()

    # Query history
    if st.session_state.query_history:
        with st.expander("📜 Query History"):
            for i, item in enumerate(reversed(st.session_state.query_history[-5:])):
                st.markdown(f"**{i+1}.** {item['query'][:100]}... → *{item['chart_type']}*")

if __name__ == "__main__":
    main()
