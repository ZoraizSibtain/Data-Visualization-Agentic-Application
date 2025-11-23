import streamlit as st
import plotly.io as pio
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.DatabaseManager import DatabaseManager
from database.query_storage import QueryStorage
from database.csv_ingestion import ingest_csv
from database.etl_3nf import ETLPipeline
from agents.workflow_manager import WorkflowManager
from config import DATABASE_URL
from utils.sidebar import render_sidebar

# Load API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

st.set_page_config(
    page_title="Chat - Agentic Data Analysis",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Chat")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'database_initialized' not in st.session_state:
    st.session_state.database_initialized = False
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = None
if 'workflow' not in st.session_state:
    st.session_state.workflow = None
if 'query_storage' not in st.session_state:
    st.session_state.query_storage = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = OPENAI_API_KEY if OPENAI_API_KEY else None

# Render shared sidebar navigation
render_sidebar()

# Sidebar - Chat specific controls
with st.sidebar:
    # Chat Sessions Section
    st.markdown('<div style="font-weight: bold; color: #ccc; margin-bottom: 0.5rem; text-transform: uppercase; font-size: 0.8rem;">Chat Sessions</div>', unsafe_allow_html=True)

    # Initialize database manager first for sessions
    if st.session_state.db_manager is None:
        try:
            st.session_state.db_manager = DatabaseManager(DATABASE_URL)
            if st.session_state.db_manager.test_connection():
                st.session_state.database_initialized = True
                st.session_state.query_storage = QueryStorage(DATABASE_URL)
        except Exception as e:
            st.error(f"Database error: {e}")

    if st.session_state.query_storage:
        # Create new session button
        if st.button("➕ New Chat", use_container_width=True):
            session_id = st.session_state.query_storage.create_session()
            st.session_state.current_session_id = session_id
            st.session_state.messages = []
            st.rerun()

        # List sessions
        sessions = st.session_state.query_storage.get_sessions()
        for session in sessions:
            # Check if we're in rename mode for this session
            if st.session_state.get(f"renaming_{session['id']}", False):
                # Inline text input for renaming - pressing Enter saves
                new_name = st.text_input(
                    "Rename session",
                    value=session['name'],
                    key=f"new_name_{session['id']}",
                    label_visibility="collapsed",
                    on_change=lambda sid=session['id']: (
                        st.session_state.query_storage.rename_session(
                            sid,
                            st.session_state.get(f"new_name_{sid}", session['name'])
                        ),
                        st.session_state.__setitem__(f"renaming_{sid}", False)
                    )
                )
                # Also allow clicking away to cancel
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✓", key=f"save_{session['id']}", use_container_width=True):
                        st.session_state.query_storage.rename_session(session['id'], new_name)
                        st.session_state[f"renaming_{session['id']}"] = False
                        st.rerun()
                with col2:
                    if st.button("✕", key=f"cancel_{session['id']}", use_container_width=True):
                        st.session_state[f"renaming_{session['id']}"] = False
                        st.rerun()
            else:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    # Double-click simulation: click to select, click again to rename
                    btn_key = f"session_{session['id']}"
                    if st.button(session['name'][:20], key=btn_key, use_container_width=True):
                        # Check if this was a recent click (double-click detection)
                        import time
                        last_click = st.session_state.get(f"last_click_{session['id']}", 0)
                        current_time = time.time()

                        if current_time - last_click < 0.5 and st.session_state.current_session_id == session['id']:
                            # Double-click: enter rename mode
                            st.session_state[f"renaming_{session['id']}"] = True
                            st.rerun()
                        else:
                            # Single click: select session
                            st.session_state[f"last_click_{session['id']}"] = current_time
                            st.session_state.current_session_id = session['id']
                            queries = st.session_state.query_storage.get_session_queries(session['id'])
                            st.session_state.messages = []
                            for q in queries:
                                st.session_state.messages.append({"role": "user", "content": q['user_question']})
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": q['result_text'] or "Response generated",
                                    "query_id": q['id'],
                                    "sql_query": q['sql_query'],
                                    "python_code": q['python_code'],
                                    "figure_json": q['figure_json'],
                                    "execution_time": q['execution_time'],
                                    "feedback": q['feedback']
                                })
                            st.rerun()
                with col2:
                    if st.button("✏️", key=f"rename_{session['id']}"):
                        st.session_state[f"renaming_{session['id']}"] = True
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"delete_{session['id']}"):
                        st.session_state.query_storage.delete_session(session['id'])
                        if st.session_state.current_session_id == session['id']:
                            st.session_state.current_session_id = None
                            st.session_state.messages = []
                        st.rerun()

        if not sessions:
            session_id = st.session_state.query_storage.create_session()
            st.session_state.current_session_id = session_id
            st.rerun()
        elif st.session_state.current_session_id is None:
            st.session_state.current_session_id = sessions[0]['id']

    st.markdown("---")

    # Database Status Section (Dropdown)
    st.markdown('<div style="font-weight: bold; color: #ccc; margin-bottom: 0.5rem; text-transform: uppercase; font-size: 0.8rem;">Database</div>', unsafe_allow_html=True)

    # Database status dropdown
    if st.session_state.database_initialized:
        db_status = "Connected"
        status_color = "green"
        tables = st.session_state.db_manager.get_table_names()
    else:
        db_status = "Disconnected"
        status_color = "red"
        tables = []

    with st.expander(f"⚡ Status: :{status_color}[{db_status}]", expanded=False):
        st.write(f"**Current DB**: PostgreSQL")
        if tables:
            st.caption(f"{len(tables)} tables available")
        if st.session_state.database_initialized:
            with st.container():
                schema = st.session_state.db_manager.get_schema()
                st.code(schema, language='text')

    with st.expander("📂 Upload Data", expanded=False):
        uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
        if uploaded_file:
            if st.button("Load CSV"):
                with st.spinner("Loading data..."):
                    temp_path = f"/tmp/{uploaded_file.name}"
                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_file.getvalue())

                    try:
                        etl = ETLPipeline(DATABASE_URL)
                        etl.drop_tables()
                        etl.create_tables()
                        etl.transform_and_load(temp_path)
                        etl.close()

                        st.session_state.database_initialized = True
                        st.success("Data loaded!")
                        st.rerun()
                    except Exception as e:
                        try:
                            table_name = ingest_csv(temp_path, database_url=DATABASE_URL)
                            st.success(f"Loaded as table: {table_name}")
                            st.rerun()
                        except Exception as e2:
                            st.error(f"Error: {e2}")

    with st.expander("⚙️ API Configuration", expanded=False):
        api_key = st.text_input("OpenAI API Key", type="password", value=st.session_state.api_key or "")
        if api_key:
            st.session_state.api_key = api_key
            st.success("API key set!")

    with st.expander("🧹 Clear Cache", expanded=False):
        st.caption("Clear cached queries and temp files")
        if st.button("Clear All Cache", use_container_width=True, key="chat_clear_cache"):
            # Clear workflow cache
            if st.session_state.workflow:
                st.session_state.workflow._cache = {}
            # Clear Streamlit cache
            st.cache_data.clear()
            st.success("Cache cleared!")
            st.rerun()

# Main chat area
if not st.session_state.api_key:
    st.warning("Please enter your OpenAI API key in the sidebar to start chatting.")
elif not st.session_state.database_initialized:
    st.warning("Please connect to a database or upload a CSV file to start.")
else:
    # Initialize workflow
    if st.session_state.workflow is None and st.session_state.api_key:
        st.session_state.workflow = WorkflowManager(st.session_state.api_key, DATABASE_URL)

    # Check for selected query from Home page
    if 'selected_query' in st.session_state and st.session_state.selected_query:
        query_to_run = st.session_state.selected_query
        st.session_state.selected_query = None  # Clear it
        
        # Add to messages
        st.session_state.messages.append({"role": "user", "content": query_to_run})
        
        # Run immediately
        with st.spinner(f"Running sample query: {query_to_run}..."):
            # Get schema
            schema = st.session_state.db_manager.get_schema()
            # Run workflow
            result = st.session_state.workflow.run(query_to_run, schema)
            
            # Save to database
            query_id = st.session_state.query_storage.save_query(
                session_id=st.session_state.current_session_id,
                user_question=query_to_run,
                sql_query=result.get("sql_query"),
                python_code=result.get("python_code"),
                result_text=result["response"],
                figure_json=result.get("figure_json"),
                execution_time=result.get("execution_time")
            )
            
            # Add to messages
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "query_id": query_id,
                "sql_query": result.get("sql_query"),
                "python_code": result.get("python_code"),
                "figure_json": result.get("figure_json"),
                "execution_time": result.get("execution_time"),
                "feedback": "none"
            })
            st.rerun()

    # Display chat history
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                # Display figure if available
                if message.get("figure_json"):
                    try:
                        fig = pio.from_json(message["figure_json"])
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error displaying chart: {e}")

                # Display text response
                st.write(message["content"])

                # Show code in expander
                with st.expander("View Python Code"):
                    st.code(message.get("python_code", "N/A"), language='python')

                # Feedback and save buttons
                if message.get("query_id"):
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
                    with col1:
                        current_feedback = message.get("feedback", "none")
                        if st.button("👍", key=f"like_{i}",
                                    type="primary" if current_feedback == "like" else "secondary"):
                            st.session_state.query_storage.update_feedback(message["query_id"], "like")
                            st.session_state.messages[i]["feedback"] = "like"
                            st.rerun()
                    with col2:
                        if st.button("👎", key=f"dislike_{i}",
                                    type="primary" if current_feedback == "dislike" else "secondary"):
                            st.session_state.query_storage.update_feedback(message["query_id"], "dislike")
                            st.session_state.messages[i]["feedback"] = "dislike"
                            st.rerun()
                    with col3:
                        if st.button("💾 Save", key=f"save_{i}"):
                            st.session_state.query_storage.mark_as_saved(message["query_id"], True)
                            st.success("Saved!")

                # Execution time
                if message.get("execution_time"):
                    st.caption(f"Execution time: {message['execution_time']:.2f}s")

    # Chat input
    if prompt := st.chat_input("Ask a question about your data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.write(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                # Get schema
                schema = st.session_state.db_manager.get_schema()

                # Run workflow
                result = st.session_state.workflow.run(prompt, schema)

                # Display figure
                if result.get("figure_json"):
                    try:
                        fig = pio.from_json(result["figure_json"])
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error displaying chart: {e}")

                # Display response
                st.write(result["response"])

                # Show code
                with st.expander("View Python Code"):
                    st.code(result.get("python_code", "N/A"), language='python')

                # Save to database
                query_id = st.session_state.query_storage.save_query(
                    session_id=st.session_state.current_session_id,
                    user_question=prompt,
                    sql_query=result.get("sql_query"),
                    python_code=result.get("python_code"),
                    result_text=result["response"],
                    figure_json=result.get("figure_json"),
                    execution_time=result.get("execution_time")
                )

                # Add to messages
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["response"],
                    "query_id": query_id,
                    "sql_query": result.get("sql_query"),
                    "python_code": result.get("python_code"),
                    "figure_json": result.get("figure_json"),
                    "execution_time": result.get("execution_time"),
                    "feedback": "none"
                })

                # Execution time
                st.caption(f"Execution time: {result.get('execution_time', 0):.2f}s")
