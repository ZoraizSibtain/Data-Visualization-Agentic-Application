"""
Chat Page - Main interface for asking questions
"""
import streamlit as st
import os
from dotenv import load_dotenv
import plotly.graph_objects as go
import json
from pathlib import Path
import datetime

# Load environment variables
load_dotenv()

# Import local modules
import config
from database.DatabaseManager import DatabaseManager
from database.csv_ingestion import ingest_csv
from database.database_setup import initialize_database
from database.query_storage import QueryStorage
from agents.workflow_manager import create_workflow
from utils.sql_extractor import format_sql

# Page configuration
st.set_page_config(
    page_title="Chat - Agentic Data Analysis",
    page_icon="💬",
    layout="wide"
)


def init_session_state():
    """Initialize session state variables"""
    if 'query_storage' not in st.session_state:
        st.session_state.query_storage = QueryStorage()
    
    # Initialize current session if not set
    if 'current_session_id' not in st.session_state:
        # Try to get most recent session
        sessions = st.session_state.query_storage.get_sessions()
        if sessions:
            st.session_state.current_session_id = sessions[0]['id']
        else:
            # Create default session
            st.session_state.current_session_id = st.session_state.query_storage.create_session("New Chat")
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        load_chat_history()
            
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = None
    if 'workflow' not in st.session_state:
        st.session_state.workflow = None
    if 'database_initialized' not in st.session_state:
        st.session_state.database_initialized = False


def load_chat_history():
    """Load chat history for current session"""
    try:
        session_id = st.session_state.current_session_id
        recent_queries = st.session_state.query_storage.get_all_queries(limit=50, session_id=session_id)
        st.session_state.messages = []
        
        # Convert database queries to chat messages
        for query in reversed(recent_queries):  # Reverse to get chronological order
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": query['user_question']
            })
            
            # Add assistant message
            assistant_msg = {
                "role": "assistant",
                "content": query['result_text'] or "I processed your question.",
                "query_id": query['id'],
                "feedback": query.get('feedback', 'none'),
                "is_saved": query.get('is_saved', False)
            }
            
            if query['figure_json']:
                assistant_msg['figure'] = query['figure_json']
            
            st.session_state.messages.append(assistant_msg)
    except Exception as e:
        st.error(f"Error loading history: {e}")
        st.session_state.messages = []


def get_api_key():
    """Get OpenAI API key from session state or environment"""
    if 'api_key' in st.session_state and st.session_state.api_key:
        return st.session_state.api_key
    return os.getenv('OPENAI_API_KEY')


def initialize_database_if_needed():
    """Initialize database with default data if not already done"""
    if not st.session_state.database_initialized:
        try:
            result = initialize_database()
            st.session_state.db_manager = DatabaseManager()
            st.session_state.database_initialized = True
            return True, result
        except Exception as e:
            return False, f"Error initializing database: {str(e)}"
    return True, "Database already initialized"


def handle_csv_upload(uploaded_file):
    """Handle CSV file upload and ingestion"""
    try:
        temp_path = config.DATA_DIR / uploaded_file.name
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        result = ingest_csv(str(temp_path))
        st.session_state.db_manager = DatabaseManager()
        st.session_state.workflow = None
        
        return True, result
    except Exception as e:
        return False, f"Error uploading CSV: {str(e)}"


def get_or_create_workflow():
    """Get existing workflow or create new one"""
    api_key = get_api_key()
    
    if not api_key:
        return None, "Please provide an OpenAI API key"
    
    if st.session_state.workflow is None:
        try:
            schema = st.session_state.db_manager.get_schema()
            workflow = create_workflow(
                api_key=api_key,
                database_url=str(config.DATABASE_URL),
                schema=schema
            )
            st.session_state.workflow = workflow
            return workflow, None
        except Exception as e:
            return None, f"Error creating workflow: {str(e)}"
    
    return st.session_state.workflow, None


def main():
    """Main application"""
    
    init_session_state()
    
    # Auto-initialize database on first run
    if not st.session_state.database_initialized:
        try:
            result = initialize_database()
            st.session_state.db_manager = DatabaseManager()
            st.session_state.database_initialized = True
        except Exception as e:
            st.error(f"Error auto-initializing database: {str(e)}")
    
    # Header
    st.title("💬 Chat with Your Data")
    st.markdown("Ask questions in natural language and get intelligent visualizations")
    
    # Sidebar
    with st.sidebar:
        st.header("💬 Chat Sessions")
        
        # Session Management
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("➕ New Chat", use_container_width=True):
                new_id = st.session_state.query_storage.create_session(f"Chat {datetime.datetime.now().strftime('%H:%M')}")
                st.session_state.current_session_id = new_id
                st.session_state.messages = []
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear", help="Delete current session", use_container_width=True):
                st.session_state.query_storage.delete_session(st.session_state.current_session_id)
                del st.session_state.current_session_id
                st.rerun()

        # Session Selector
        sessions = st.session_state.query_storage.get_sessions()
        session_options = {s['id']: f"{s['name']} ({s['created_at'].strftime('%m/%d %H:%M')})" for s in sessions}
        
        selected_session_id = st.selectbox(
            "Switch Chat",
            options=list(session_options.keys()),
            format_func=lambda x: session_options[x],
            index=list(session_options.keys()).index(st.session_state.current_session_id) if st.session_state.current_session_id in session_options else 0,
            key="session_selector"
        )
        
        if selected_session_id != st.session_state.current_session_id:
            st.session_state.current_session_id = selected_session_id
            load_chat_history()
            st.rerun()
            
        # Rename Session
        with st.expander("✏️ Rename Chat"):
            current_name = next((s['name'] for s in sessions if s['id'] == st.session_state.current_session_id), "New Chat")
            new_name = st.text_input("New Name", value=current_name)
            if st.button("Update Name"):
                if new_name and new_name != current_name:
                    st.session_state.query_storage.rename_session(st.session_state.current_session_id, new_name)
                    st.rerun()

        st.divider()
        
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get('api_key', ''),
            help="Enter your OpenAI API key or set OPENAI_API_KEY environment variable"
        )
        
        if api_key_input:
            st.session_state.api_key = api_key_input
        
        api_key = get_api_key()
        if api_key:
            st.success("✅ API Key configured")
        else:
            st.warning("⚠️ Please provide an API Key")
        
        st.divider()
        
        # Database initialization
        st.header("📁 Data Source")
        
        if st.session_state.database_initialized:
            st.success("✅ Database initialized")
            
            if st.session_state.db_manager:
                tables = st.session_state.db_manager.get_table_names()
                st.info(f"📊 Tables: {', '.join(tables)}")
        else:
            st.warning("⚠️ Database not initialized")
            if st.button("Retry Initialization"):
                with st.spinner("Initializing database..."):
                    success, message = initialize_database_if_needed()
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        st.divider()
        
        # CSV Upload
        st.header("📤 Upload CSV")
        uploaded_file = st.file_uploader(
            "Upload a CSV file to analyze",
            type=['csv'],
            help="Upload a CSV file to create a new table in the database"
        )
        
        if uploaded_file is not None:
            if st.button("Process CSV"):
                with st.spinner("Processing CSV..."):
                    success, message = handle_csv_upload(uploaded_file)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        st.divider()
        
        # Database Schema
        if st.session_state.db_manager:
            with st.expander("📋 View Database Schema"):
                schema = st.session_state.db_manager.get_schema()
                st.code(schema, language="text")
    
    # Main content area - only check for API key
    if not api_key:
        st.warning("👈 Please provide an OpenAI API key in the sidebar")
        return
    
    # Chat interface
    st.header("Ask Questions About Your Data")
    
    # Display chat messages
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display visualization if present
            if "figure" in message and message["figure"]:
                try:
                    fig = go.Figure(json.loads(message["figure"]))
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error displaying chart: {str(e)}")
            
            # Feedback buttons for assistant messages
            if message["role"] == "assistant" and "query_id" in message:
                # Get current state from database to ensure we have the latest status
                # This is crucial for the buttons to reflect the correct state after a rerun
                try:
                    current_query = st.session_state.query_storage.get_queries_by_ids([message["query_id"]])
                    if current_query:
                        current_feedback = current_query[0].get('feedback', 'none')
                        current_is_saved = current_query[0].get('is_saved', False)
                    else:
                        current_feedback = message.get("feedback", "none")
                        current_is_saved = message.get("is_saved", False)
                except:
                    current_feedback = message.get("feedback", "none")
                    current_is_saved = message.get("is_saved", False)
                
                col1, col2, col3, col4 = st.columns([1, 1, 2, 8])
                
                with col1:
                    # Like button
                    button_type = "primary" if current_feedback == "like" else "secondary"
                    if st.button("👍", key=f"like_{message['query_id']}", type=button_type):
                        st.session_state.query_storage.update_feedback(message["query_id"], "like")
                        message["feedback"] = "like"
                        st.rerun()
                
                with col2:
                    # Dislike button
                    button_type = "primary" if current_feedback == "dislike" else "secondary"
                    if st.button("👎", key=f"dislike_{message['query_id']}", type=button_type):
                        st.session_state.query_storage.update_feedback(message["query_id"], "dislike")
                        message["feedback"] = "dislike"
                        st.rerun()
                
                with col3:
                    # Save query button
                    if current_is_saved:
                        st.success("✅ Saved")
                    else:
                        if st.button("💾 Save Query", key=f"save_{message['query_id']}"):
                            st.session_state.query_storage.mark_as_saved(message["query_id"])
                            message["is_saved"] = True
                            st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get or create workflow
        workflow, error = get_or_create_workflow()
        
        if error:
            with st.chat_message("assistant"):
                st.error(error)
            return
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your question..."):
                try:
                    result = workflow.run_query(prompt)
                    
                    # Display response
                    st.markdown(result['response'])
                    
                    # Save to database
                    query_id = st.session_state.query_storage.save_query(
                        user_question=prompt,
                        sql_query=result.get('sql_query'),
                        python_code=result.get('code'),
                        result_text=result.get('response'),
                        figure_json=result.get('figure_json'),
                        execution_time=result.get('execution_time'),
                        is_saved=False,
                        session_id=st.session_state.current_session_id
                    )
                    
                    # Display visualization if available
                    if result['figure_json']:
                        try:
                            fig = go.Figure(json.loads(result['figure_json']))
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Save to message history with feedback and saved state
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": result['response'],
                                "figure": result['figure_json'],
                                "query_id": query_id,
                                "feedback": "none",
                                "is_saved": False
                            })
                        except Exception as e:
                            st.error(f"Error displaying visualization: {str(e)}")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": result['response'],
                                "query_id": query_id,
                                "feedback": "none",
                                "is_saved": False
                            })
                    else:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result['response'],
                            "query_id": query_id,
                            "feedback": "none",
                            "is_saved": False
                        })
                    
                    # SQL query is already shown in generated code, so we skip this
                    
                    # Show generated code
                    if result['code']:
                        with st.expander("💻 View Generated Code"):
                            st.code(result['code'], language="python")
                    
                    # Show execution time
                    if result.get('execution_time'):
                        st.caption(f"⏱️ Execution time: {result['execution_time']:.2f}s")
                    
                    # Feedback and Save buttons
                    col1, col2, col3, col4 = st.columns([1, 1, 2, 8])
                    
                    # Get current state from database
                    current_query = st.session_state.query_storage.get_queries_by_ids([query_id])
                    if current_query:
                        current_feedback = current_query[0].get('feedback', 'none')
                        current_is_saved = current_query[0].get('is_saved', False)
                    else:
                        current_feedback = 'none'
                        current_is_saved = False
                    
                    with col1:
                        # Like button
                        button_type = "primary" if current_feedback == "like" else "secondary"
                        if st.button("👍", key=f"like_new_{query_id}", type=button_type):
                            st.session_state.query_storage.update_feedback(query_id, "like")
                            # Update message in session state
                            for msg in st.session_state.messages:
                                if msg.get("query_id") == query_id:
                                    msg["feedback"] = "like"
                            st.rerun()
                    
                    with col2:
                        # Dislike button
                        button_type = "primary" if current_feedback == "dislike" else "secondary"
                        if st.button("👎", key=f"dislike_new_{query_id}", type=button_type):
                            st.session_state.query_storage.update_feedback(query_id, "dislike")
                            # Update message in session state
                            for msg in st.session_state.messages:
                                if msg.get("query_id") == query_id:
                                    msg["feedback"] = "dislike"
                            st.rerun()
                    
                    with col3:
                        # Save query button
                        if current_is_saved:
                            st.success("✅ Saved")
                        else:
                            if st.button("💾 Save Query", key=f"save_new_{query_id}"):
                                st.session_state.query_storage.mark_as_saved(query_id)
                                # Update message in session state
                                for msg in st.session_state.messages:
                                    if msg.get("query_id") == query_id:
                                        msg["is_saved"] = True
                                st.rerun()
                    
                    # Show error if any
                    if result['error']:
                        st.warning(f"Note: {result['error']}")
                
                except Exception as e:
                    error_msg = f"Error processing query: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })


if __name__ == "__main__":
    main()
