import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

class ChartRenderer:
    @staticmethod
    def render_chart(df: pd.DataFrame, chart_type: str):
        if df is None or df.empty:
            return None
            
        try:
            if chart_type == "line":
                # Heuristic: Assume first column is x-axis (often date), second is y-axis (metric)
                if len(df.columns) < 2:
                    return None
                x_col = df.columns[0]
                y_cols = list(df.columns[1:])
                # Convert to list for single column case
                if len(y_cols) == 1:
                    y_cols = y_cols[0]
                fig = px.line(df, x=x_col, y=y_cols, title="Trend Analysis", markers=True)
                
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

                fig = px.bar(df, x=x_col, y=y_col, title="Comparison Analysis")
                    
            elif chart_type == "pie":
                # Heuristic: First categorical as names, first numerical as values
                if len(df.columns) < 2:
                    return None
                # Try to find categorical and numeric columns
                cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns
                num_cols = df.select_dtypes(include=['number']).columns

                if len(cat_cols) > 0 and len(num_cols) > 0:
                    names_col = cat_cols[0]
                    values_col = num_cols[0]
                else:
                    # Fallback: assume first column is names, second is values
                    names_col = df.columns[0]
                    values_col = df.columns[1]

                fig = px.pie(df, names=names_col, values=values_col, title="Distribution Analysis")

            elif chart_type == "scatter":
                # Heuristic: First two numerical columns
                num_cols = df.select_dtypes(include=['number']).columns
                if len(num_cols) >= 2:
                    fig = px.scatter(df, x=num_cols[0], y=num_cols[1], title="Correlation Analysis")
                else:
                    fig = px.scatter(df, x=df.columns[0], y=df.columns[1], title="Correlation Analysis")
            
            else:
                return None

            return fig
            
        except Exception as e:
            print(f"Error rendering chart: {e}")
            return None
