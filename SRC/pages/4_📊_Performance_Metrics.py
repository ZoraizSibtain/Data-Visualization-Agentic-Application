import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.query_storage import QueryStorage
from config import DATABASE_URL
from utils.sidebar import render_sidebar

st.set_page_config(
    page_title="Performance Metrics - Agentic Data Analysis",
    page_icon="📊",
    layout="wide"
)

# Render shared sidebar
render_sidebar()

st.title("📊 Performance Metrics")

# Initialize query storage
if 'query_storage' not in st.session_state or st.session_state.query_storage is None:
    try:
        st.session_state.query_storage = QueryStorage(DATABASE_URL)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.stop()

query_storage = st.session_state.query_storage

# Get metrics
metrics = query_storage.get_performance_metrics()

# Key metrics
st.markdown("### Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Queries",
        metrics['total_queries'],
        help="Total number of queries executed"
    )

with col2:
    st.metric(
        "Avg Execution Time",
        f"{metrics['avg_execution_time']:.2f}s",
        help="Average query execution time in seconds"
    )

with col3:
    st.metric(
        "Satisfaction Rate",
        f"{metrics['satisfaction_rate']:.1f}%",
        help="Percentage of liked queries out of all rated queries"
    )

with col4:
    st.metric(
        "Saved Queries",
        metrics['saved_count'],
        help="Number of queries marked as saved"
    )

st.markdown("---")

# Feedback distribution
st.markdown("### Feedback Distribution")

col1, col2 = st.columns(2)

with col1:
    # Pie chart of feedback
    feedback_data = {
        'Feedback': ['Liked', 'Disliked', 'No Feedback'],
        'Count': [
            metrics['likes'],
            metrics['dislikes'],
            metrics['total_queries'] - metrics['likes'] - metrics['dislikes']
        ]
    }
    df_feedback = pd.DataFrame(feedback_data)

    fig = px.pie(
        df_feedback,
        values='Count',
        names='Feedback',
        title='Query Feedback Distribution',
        color='Feedback',
        color_discrete_map={
            'Liked': '#4CAF50',
            'Disliked': '#F44336',
            'No Feedback': '#9E9E9E'
        }
    )
    fig.update_layout(template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Bar chart of metrics
    metric_data = {
        'Metric': ['Total Queries', 'Saved', 'Liked', 'Disliked'],
        'Value': [
            metrics['total_queries'],
            metrics['saved_count'],
            metrics['likes'],
            metrics['dislikes']
        ]
    }
    df_metrics = pd.DataFrame(metric_data)

    fig = px.bar(
        df_metrics,
        x='Metric',
        y='Value',
        title='Query Statistics',
        color='Value',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Get all queries for additional analysis
queries = query_storage.get_all_queries(limit=1000)

if queries:
    st.markdown("### Query Analysis")

    # Execution time distribution
    col1, col2 = st.columns(2)

    with col1:
        exec_times = [q['execution_time'] for q in queries if q['execution_time']]
        if exec_times:
            fig = px.histogram(
                x=exec_times,
                nbins=20,
                title='Execution Time Distribution',
                labels={'x': 'Execution Time (s)', 'y': 'Count'}
            )
            fig.update_layout(template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No execution time data available")

    with col2:
        # Queries over time
        timestamps = [q['timestamp'] for q in queries if q['timestamp']]
        if timestamps:
            df_time = pd.DataFrame({'timestamp': timestamps})
            df_time['date'] = pd.to_datetime(df_time['timestamp']).dt.date
            df_daily = df_time.groupby('date').size().reset_index(name='count')

            fig = px.line(
                df_daily,
                x='date',
                y='count',
                title='Queries Over Time',
                labels={'date': 'Date', 'count': 'Number of Queries'}
            )
            fig.update_layout(template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timestamp data available")

    # Additional stats
    st.markdown("### Summary Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        if exec_times:
            st.metric("Min Execution Time", f"{min(exec_times):.2f}s")
            st.metric("Max Execution Time", f"{max(exec_times):.2f}s")
        else:
            st.info("No execution data")

    with col2:
        with_viz = sum(1 for q in queries if q['figure_json'])
        st.metric("Queries with Visualization", with_viz)
        st.metric("Visualization Rate", f"{(with_viz / len(queries) * 100):.1f}%" if queries else "0%")

    with col3:
        with_sql = sum(1 for q in queries if q['sql_query'])
        st.metric("Queries with SQL", with_sql)
        st.metric("SQL Generation Rate", f"{(with_sql / len(queries) * 100):.1f}%" if queries else "0%")

else:
    st.info("No queries found. Start chatting to generate performance data!")
