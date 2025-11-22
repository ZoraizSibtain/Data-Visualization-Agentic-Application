"""
Saved Queries Page - Manage and export saved queries
"""
import streamlit as st
from database.query_storage import QueryStorage
from utils.pdf_generator import PDFReportGenerator
import plotly.graph_objects as go
import json
from datetime import datetime

st.set_page_config(
    page_title="Saved Queries - Agentic Data Analysis",
    page_icon="💾",
    layout="wide"
)

# Initialize
if 'query_storage' not in st.session_state:
    st.session_state.query_storage = QueryStorage()

st.title("💾 Saved Queries")

col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("Manage your saved queries and generate PDF reports")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

st.divider()

# Get saved queries
try:
    saved_queries = st.session_state.query_storage.get_saved_queries()
    
    if not saved_queries:
        st.info("No saved queries yet. Save queries from the Chat or History pages!")
    else:
        st.markdown(f"### {len(saved_queries)} Saved Queries")
        
        # Multi-select for PDF export
        st.markdown("#### Select queries to export to PDF:")
        
        selected_ids = []
        for query in saved_queries:
            col1, col2 = st.columns([0.5, 11.5])
            with col1:
                if st.checkbox("Select", key=f"select_{query['id']}", label_visibility="collapsed"):
                    selected_ids.append(query['id'])
            with col2:
                st.markdown(f"**{query['timestamp'].strftime('%Y-%m-%d %H:%M')}** - {query['user_question']}")
        
        st.divider()
        
        # Export buttons
        col1, col2, col3 = st.columns([2, 2, 8])
        with col1:
            if st.button("📄 Generate PDF Report", disabled=len(selected_ids) == 0):
                if selected_ids:
                    with st.spinner("Generating PDF..."):
                        try:
                            # Get selected queries
                            queries_to_export = st.session_state.query_storage.get_queries_by_ids(selected_ids)
                            
                            # Generate PDF
                            pdf_gen = PDFReportGenerator()
                            pdf_buffer = pdf_gen.generate_report(queries_to_export)
                            
                            # Download button
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=pdf_buffer,
                                file_name=f"query_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf"
                            )
                            st.success(f"PDF generated with {len(selected_ids)} queries!")
                        except Exception as e:
                            st.error(f"Error generating PDF: {str(e)}")
        
        with col2:
            if st.button("🗑️ Delete Selected", disabled=len(selected_ids) == 0):
                if selected_ids:
                    for query_id in selected_ids:
                        st.session_state.query_storage.delete_query(query_id)
                    st.success(f"Deleted {len(selected_ids)} queries!")
                    st.rerun()
        
        st.divider()
        
        # Display saved queries
        st.markdown("### Query Details")
        
        for query in saved_queries:
            with st.expander(f"🕐 {query['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {query['user_question'][:80]}..."):
                # Question
                st.markdown(f"**Question:** {query['user_question']}")
                
                # SQL Query
                if query['sql_query']:
                    st.markdown("**SQL Query:**")
                    st.code(query['sql_query'], language="sql")
                
                # Python Code (removed nested expander to fix error)
                if query['python_code']:
                    st.markdown("**Python Code:**")
                    st.code(query['python_code'], language="python")
                
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
                
                # Notes
                notes = st.text_area(
                    "📝 Notes",
                    value=query.get('notes', ''),
                    key=f"notes_{query['id']}",
                    placeholder="Add notes about this query..."
                )
                
                if st.button("💾 Update Notes", key=f"update_notes_{query['id']}"):
                    st.session_state.query_storage.mark_as_saved(query['id'], notes=notes)
                    st.success("Notes updated!")
                
                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{query['id']}"):
                    st.session_state.query_storage.delete_query(query['id'])
                    st.success("Query deleted!")
                    st.rerun()
                
                # Feedback
                if query['feedback'] != 'none':
                    feedback_emoji = '👍' if query['feedback'] == 'like' else '👎'
                    st.caption(f"Feedback: {feedback_emoji}")

except Exception as e:
    st.error(f"Error loading saved queries: {str(e)}")
