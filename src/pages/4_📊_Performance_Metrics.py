"""
Performance Metrics Page - Analytics dashboard
"""
import streamlit as st
from database.query_storage import QueryStorage
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Performance Metrics - Agentic Data Analysis",
    page_icon="📊",
    layout="wide"
)

# Initialize
if 'query_storage' not in st.session_state:
    st.session_state.query_storage = QueryStorage()

st.title("📊 Performance Metrics")
st.markdown("Track analytics and user feedback")

# Get metrics
try:
    metrics = st.session_state.query_storage.get_performance_metrics()
    all_queries = st.session_state.query_storage.get_all_queries(limit=1000)
    
    # Overview metrics
    st.markdown("### 📈 Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Queries", metrics['total_queries'])
    
    with col2:
        st.metric("Avg Response Time", f"{metrics['avg_execution_time']:.2f}s")
    
    with col3:
        satisfaction = metrics['satisfaction_rate']
        st.metric("Satisfaction Rate", f"{satisfaction:.1f}%")
    
    with col4:
        st.metric("Saved Queries", metrics['saved_count'])
    
    st.divider()
    
    # Feedback Distribution
    st.markdown("### 👍👎 User Feedback")
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart for feedback
        feedback_data = pd.DataFrame({
            'Feedback': ['Likes', 'Dislikes', 'No Feedback'],
            'Count': [
                metrics['likes'],
                metrics['dislikes'],
                metrics['total_queries'] - metrics['likes'] - metrics['dislikes']
            ]
        })
        
        fig_feedback = px.pie(
            feedback_data,
            values='Count',
            names='Feedback',
            title='Feedback Distribution',
            color='Feedback',
            color_discrete_map={
                'Likes': '#2ca02c',
                'Dislikes': '#d62728',
                'No Feedback': '#7f7f7f'
            }
        )
        st.plotly_chart(fig_feedback, use_container_width=True)
    
    with col2:
        # Bar chart for feedback counts
        fig_bar = go.Figure(data=[
            go.Bar(name='Likes', x=['Feedback'], y=[metrics['likes']], marker_color='#2ca02c'),
            go.Bar(name='Dislikes', x=['Feedback'], y=[metrics['dislikes']], marker_color='#d62728')
        ])
        fig_bar.update_layout(
            title='Likes vs Dislikes',
            yaxis_title='Count',
            barmode='group'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()
    
    # Query Volume Over Time
    st.markdown("### 📅 Query Volume Over Time")
    
    if all_queries:
        # Group by date
        query_dates = [q['timestamp'].date() for q in all_queries]
        date_counts = pd.Series(query_dates).value_counts().sort_index()
        
        df_timeline = pd.DataFrame({
            'Date': date_counts.index,
            'Queries': date_counts.values
        })
        
        fig_timeline = px.line(
            df_timeline,
            x='Date',
            y='Queries',
            title='Queries Per Day',
            markers=True
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No query data available yet")
    
    st.divider()
    
    # Execution Time Statistics
    st.markdown("### ⏱️ Execution Time Analysis")
    
    if all_queries:
        execution_times = [q['execution_time'] for q in all_queries if q['execution_time']]
        
        if execution_times:
            col1, col2 = st.columns(2)
            
            with col1:
                # Histogram
                fig_hist = px.histogram(
                    execution_times,
                    nbins=20,
                    title='Execution Time Distribution',
                    labels={'value': 'Execution Time (s)', 'count': 'Frequency'}
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Box plot
                fig_box = px.box(
                    y=execution_times,
                    title='Execution Time Statistics',
                    labels={'y': 'Execution Time (s)'}
                )
                st.plotly_chart(fig_box, use_container_width=True)
            
            # Statistics table
            stats_df = pd.DataFrame({
                'Metric': ['Min', 'Max', 'Mean', 'Median', 'Std Dev'],
                'Value (seconds)': [
                    f"{min(execution_times):.2f}",
                    f"{max(execution_times):.2f}",
                    f"{sum(execution_times)/len(execution_times):.2f}",
                    f"{sorted(execution_times)[len(execution_times)//2]:.2f}",
                    f"{pd.Series(execution_times).std():.2f}"
                ]
            })
            st.table(stats_df)
        else:
            st.info("No execution time data available")
    else:
        st.info("No query data available yet")
    
    st.divider()
    
    # Recent Activity
    st.markdown("### 🕐 Recent Activity")
    
    recent_queries = all_queries[:10]
    if recent_queries:
        for query in recent_queries:
            feedback_emoji = ""
            if query['feedback'] == 'like':
                feedback_emoji = "👍"
            elif query['feedback'] == 'dislike':
                feedback_emoji = "👎"
            
            saved_badge = "💾" if query['is_saved'] else ""
            
            st.markdown(
                f"**{query['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}** {feedback_emoji} {saved_badge} - "
                f"{query['user_question'][:100]}..."
            )
    else:
        st.info("No recent activity")

except Exception as e:
    st.error(f"Error loading metrics: {str(e)}")
