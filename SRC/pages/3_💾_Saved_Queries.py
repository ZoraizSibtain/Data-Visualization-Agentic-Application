import streamlit as st
import plotly.io as pio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.query_storage import QueryStorage
from utils.pdf_generator import generate_pdf_report
from config import DATABASE_URL

st.set_page_config(
    page_title="Saved Queries - Agentic Data Analysis",
    page_icon="💾",
    layout="wide"
)

st.title("💾 Saved Queries")

# Initialize query storage
if 'query_storage' not in st.session_state or st.session_state.query_storage is None:
    try:
        st.session_state.query_storage = QueryStorage(DATABASE_URL)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.stop()

query_storage = st.session_state.query_storage

# Get saved queries
queries = query_storage.get_saved_queries()

if not queries:
    st.info("No saved queries yet. Save queries from the Chat or History pages.")
else:
    # Batch actions
    st.markdown("### Batch Actions")

    # Initialize selected queries in session state
    if 'selected_queries' not in st.session_state:
        st.session_state.selected_queries = set()

    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

    with col1:
        if st.button("Select All"):
            st.session_state.selected_queries = {q['id'] for q in queries}
            st.rerun()

    with col2:
        if st.button("Deselect All"):
            st.session_state.selected_queries = set()
            st.rerun()

    with col3:
        if st.button("📄 Generate PDF Report"):
            if st.session_state.selected_queries:
                selected_queries = [q for q in queries if q['id'] in st.session_state.selected_queries]
                pdf_bytes = generate_pdf_report(selected_queries, "Saved Queries Report")
                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name="query_report.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("Please select queries first")

    with col4:
        if st.button("🗑️ Delete Selected"):
            if st.session_state.selected_queries:
                for query_id in st.session_state.selected_queries:
                    query_storage.delete_query(query_id)
                st.session_state.selected_queries = set()
                st.success("Deleted!")
                st.rerun()

    st.markdown("---")
    st.markdown(f"**{len(queries)} saved queries**")

    # Display queries
    for i, query in enumerate(queries):
        col1, col2 = st.columns([1, 20])

        with col1:
            # Checkbox for selection
            is_selected = query['id'] in st.session_state.selected_queries
            if st.checkbox("Select", value=is_selected, key=f"select_{query['id']}", label_visibility="collapsed"):
                st.session_state.selected_queries.add(query['id'])
            else:
                st.session_state.selected_queries.discard(query['id'])

        with col2:
            timestamp = query['timestamp'].strftime('%Y-%m-%d %H:%M') if query['timestamp'] else 'Unknown'
            feedback_emoji = ""
            if query['feedback'] == 'like':
                feedback_emoji = " 👍"
            elif query['feedback'] == 'dislike':
                feedback_emoji = " 👎"

            with st.expander(f"{timestamp} - {query['user_question'][:80]}{feedback_emoji}"):
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
                    if st.toggle("View Python Code", key=f"toggle_code_{query['id']}"):
                        st.code(query['python_code'], language='python')

                # Notes
                st.markdown("**Notes:**")
                notes = st.text_area(
                    "Add notes",
                    value=query['notes'] or "",
                    key=f"notes_{query['id']}",
                    placeholder="Add notes about this query..."
                )

                col1, col2, col3 = st.columns([2, 2, 4])
                with col1:
                    if st.button("Save Notes", key=f"save_notes_{query['id']}"):
                        query_storage.update_notes(query['id'], notes)
                        st.success("Notes saved!")

                with col2:
                    if st.button("Remove from Saved", key=f"unsave_{query['id']}"):
                        query_storage.mark_as_saved(query['id'], False)
                        st.rerun()

                # Metadata
                if query['execution_time']:
                    st.caption(f"Execution time: {query['execution_time']:.2f}s")
