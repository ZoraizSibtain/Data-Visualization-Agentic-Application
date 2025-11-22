"""
PDF Report Generator - Generate PDF reports from saved queries
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
import plotly.graph_objects as go
import json
from io import BytesIO
import tempfile
import os


class PDFReportGenerator:
    """Generate PDF reports from query data"""
    
    def __init__(self):
        """Initialize PDF generator"""
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2ca02c'),
            spaceAfter=12
        )
    
    def generate_report(self, queries, output_path=None):
        """
        Generate PDF report from queries
        
        Args:
            queries: List of query dictionaries
            output_path: Path to save PDF (if None, returns BytesIO)
            
        Returns:
            Path to generated PDF or BytesIO object
        """
        if output_path is None:
            output = BytesIO()
        else:
            output = output_path
        
        doc = SimpleDocTemplate(
            output,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title page
        story.append(Paragraph("Data Analysis Report", self.title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
        story.append(Paragraph(f"Total Queries: {len(queries)}", self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        temp_files = []
        
        # Add each query
        for i, query in enumerate(queries, 1):
            story.append(Paragraph(f"Query {i}", self.heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            # Question
            story.append(Paragraph(f"<b>Question:</b> {query['user_question']}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            # SQL Query
            if query.get('sql_query'):
                story.append(Paragraph("<b>SQL Query:</b>", self.styles['Normal']))
                sql_text = query['sql_query'].replace('\n', '<br/>')
                story.append(Paragraph(f"<font name='Courier' size=9>{sql_text}</font>", self.styles['Code']))
                story.append(Spacer(1, 0.1*inch))
            
            # Execution time
            if query.get('execution_time'):
                story.append(Paragraph(f"<b>Execution Time:</b> {query['execution_time']:.2f} seconds", self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            
            # Visualization
            if query.get('figure_json'):
                try:
                    # Convert Plotly figure to image
                    fig = go.Figure(json.loads(query['figure_json']))
                    
                    # Force white background and colored theme for PDF
                    fig.update_layout(template="plotly_white")
                    
                    # Create a temporary file that persists
                    import tempfile
                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    tmp_path = tmp_file.name
                    tmp_file.close()
                    temp_files.append(tmp_path)
                    
                    # Save figure to file
                    fig.write_image(tmp_path, width=600, height=400)
                    
                    # Add image to PDF
                    img = Image(tmp_path, width=5*inch, height=3.33*inch)
                    story.append(img)
                    
                except Exception as e:
                    story.append(Paragraph(f"<i>Visualization unavailable: {str(e)}</i>", self.styles['Normal']))
            
            # Feedback
            if query.get('feedback') and query['feedback'] != 'none':
                feedback_emoji = '👍' if query['feedback'] == 'like' else '👎'
                story.append(Paragraph(f"<b>Feedback:</b> {feedback_emoji}", self.styles['Normal']))
            
            # Notes
            if query.get('notes'):
                story.append(Paragraph(f"<b>Notes:</b> {query['notes']}", self.styles['Normal']))
            
            # Add page break between queries (except last one)
            if i < len(queries):
                story.append(PageBreak())
        
        # Build PDF
        try:
            doc.build(story)
        finally:
            # Clean up temp files
            for tmp_path in temp_files:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        if output_path is None:
            output.seek(0)
            return output
        else:
            return output_path
    
    def generate_summary_report(self, metrics):
        """
        Generate a summary report with performance metrics
        
        Args:
            metrics: Dictionary of performance metrics
            
        Returns:
            BytesIO object containing PDF
        """
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("Performance Metrics Summary", self.title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Metrics table
        data = [
            ['Metric', 'Value'],
            ['Total Queries', str(metrics.get('total_queries', 0))],
            ['Average Execution Time', f"{metrics.get('avg_execution_time', 0):.2f}s"],
            ['Likes', str(metrics.get('likes', 0))],
            ['Dislikes', str(metrics.get('dislikes', 0))],
            ['Satisfaction Rate', f"{metrics.get('satisfaction_rate', 0):.1f}%"],
            ['Saved Queries', str(metrics.get('saved_count', 0))]
        ]
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        doc.build(story)
        output.seek(0)
        return output
