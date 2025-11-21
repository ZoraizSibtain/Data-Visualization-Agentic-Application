import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

class ChartRenderer:
    # Custom color palette for a premium look
    COLORS = [
        "#2E86C1", "#28B463", "#D35400", "#884EA0", "#F1C40F", 
        "#17A589", "#CB4335", "#2E4053", "#7D3C98", "#D68910"
    ]
    
    TEMPLATE = "plotly_white"

    @staticmethod
    def _apply_layout(fig, title: str):
        """Apply consistent layout styling to all charts"""
        fig.update_layout(
            title={
                'text': title,
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20)
            },
            template=ChartRenderer.TEMPLATE,
            margin=dict(l=40, r=40, t=80, b=40),
            hovermode="x unified",
            font=dict(family="Inter, sans-serif")
        )
        return fig

    @staticmethod
    def render_chart(df: pd.DataFrame, chart_type: str, query_text: str = None):
        if df is None or df.empty:
            return None
            
        try:
            fig = None
            
            # Check for highlighting keywords
            highlight_max = False
            if query_text:
                keywords = ['highest', 'best', 'top', 'most', 'maximum', 'peak']
                if any(k in query_text.lower() for k in keywords):
                    highlight_max = True

            if chart_type == "line":
                # Heuristic: Assume first column is x-axis (often date), second is y-axis (metric)
                if len(df.columns) < 2:
                    return None
                x_col = df.columns[0]
                y_cols = list(df.columns[1:])
                # Convert to list for single column case
                if len(y_cols) == 1:
                    y_cols = y_cols[0]
                
                fig = px.line(
                    df, x=x_col, y=y_cols, 
                    markers=True,
                    color_discrete_sequence=ChartRenderer.COLORS
                )
                fig = ChartRenderer._apply_layout(fig, "Trend Analysis")
                fig.update_traces(line=dict(width=3), marker=dict(size=8))
                
            elif chart_type == "bar":
                # Heuristic: First categorical column as x, first numerical as y
                if len(df.columns) < 2:
                    return None
                cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns
                num_cols = df.select_dtypes(include=['number']).columns

                if len(cat_cols) > 0 and len(num_cols) > 0:
                    x_col = cat_cols[0]
                    y_col = num_cols[0]
                else:
                    # Fallback: assume first column is x, second is y
                    x_col = df.columns[0]
                    y_col = df.columns[1]

                # Convert x-axis to string to prevent numeric formatting
                df_plot = df.copy()
                df_plot[x_col] = df_plot[x_col].astype(str)
                
                # Determine colors
                colors = ChartRenderer.COLORS
                if highlight_max:
                    # Find max value index
                    try:
                        max_idx = df_plot[y_col].idxmax()
                        # Create a color list where max is distinct (e.g., Gold/Orange) and others are standard Blue
                        # Using a list of colors for each bar
                        bar_colors = ['#2E86C1'] * len(df_plot) # Default Blue
                        # Set max value to Gold/Orange
                        # We need integer position
                        pos = df_plot.index.get_loc(max_idx)
                        bar_colors[pos] = '#F39C12' # Orange/Gold
                        
                        fig = px.bar(
                            df_plot, x=x_col, y=y_col
                        )
                        fig.update_traces(marker_color=bar_colors)
                    except:
                        # Fallback if something fails
                        fig = px.bar(
                            df_plot, x=x_col, y=y_col,
                            color_discrete_sequence=ChartRenderer.COLORS
                        )
                else:
                    fig = px.bar(
                        df_plot, x=x_col, y=y_col,
                        color_discrete_sequence=ChartRenderer.COLORS
                    )
                
                fig = ChartRenderer._apply_layout(fig, "Comparison Analysis")
                    
            elif chart_type == "pie":
                # Heuristic: First categorical as names, first numerical as values
                if len(df.columns) < 2:
                    return None
                cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns
                num_cols = df.select_dtypes(include=['number']).columns

                if len(cat_cols) > 0 and len(num_cols) > 0:
                    names_col = cat_cols[0]
                    values_col = num_cols[0]
                else:
                    names_col = df.columns[0]
                    values_col = df.columns[1]

                fig = px.pie(
                    df, names=names_col, values=values_col,
                    hole=0.4,
                    color_discrete_sequence=ChartRenderer.COLORS
                )
                fig = ChartRenderer._apply_layout(fig, "Distribution Analysis")
                fig.update_traces(textposition='inside', textinfo='percent+label')

            elif chart_type == "scatter":
                # Heuristic: First two numerical columns
                num_cols = df.select_dtypes(include=['number']).columns
                if len(num_cols) >= 2:
                    fig = px.scatter(
                        df, x=num_cols[0], y=num_cols[1],
                        color_discrete_sequence=ChartRenderer.COLORS
                    )
                else:
                    fig = px.scatter(
                        df, x=df.columns[0], y=df.columns[1],
                        color_discrete_sequence=ChartRenderer.COLORS
                    )
                fig = ChartRenderer._apply_layout(fig, "Correlation Analysis")
                fig.update_traces(marker=dict(size=10, opacity=0.7))
            
            else:
                return None

            return fig
            
        except Exception as e:
            print(f"Error rendering chart: {e}")
            return None
