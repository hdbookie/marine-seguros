from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import os
import tempfile

class ExportHandler:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12
        )
        
    def export_to_pdf(self, data, insights, filename="financial_report.pdf"):
        """Export financial data and insights to PDF"""
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # Title
        story.append(Paragraph("Marine Seguros - Relatório Financeiro", self.title_style))
        story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Summary section
        story.append(Paragraph("Resumo Executivo", self.heading_style))
        summary = data['summary']
        summary_text = f"""
        Período Analisado: {summary['years_range']}<br/>
        Receita Total: R$ {summary['metrics'].get('revenue', {}).get('total', 0):,.2f}<br/>
        CAGR da Receita: {summary['metrics'].get('revenue', {}).get('cagr', 0):.1f}%<br/>
        Margem de Lucro Média: {summary['metrics'].get('profit_margin', {}).get('average', 0):.1f}%
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Financial data table
        story.append(Paragraph("Dados Financeiros Anuais", self.heading_style))
        df = data['consolidated']
        
        # Prepare table data
        table_data = [['Ano', 'Receita', 'Crescimento', 'Margem']]
        for _, row in df.iterrows():
            table_data.append([
                str(int(row['year'])),
                f"R$ {row.get('revenue', 0):,.2f}",
                f"{row.get('revenue_growth', 0):.1f}%",
                f"{row.get('profit_margin', 0):.1f}%"
            ])
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(PageBreak())
        
        # AI Insights
        if insights:
            story.append(Paragraph("Insights de IA (Gemini)", self.heading_style))
            # Convert markdown to paragraphs
            insights_lines = insights.split('\n')
            for line in insights_lines:
                if line.strip():
                    if line.startswith('#'):
                        # Header
                        clean_line = line.lstrip('#').strip()
                        story.append(Paragraph(clean_line, self.heading_style))
                    elif line.startswith('-') or line.startswith('*'):
                        # Bullet point
                        clean_line = '• ' + line.lstrip('-*').strip()
                        story.append(Paragraph(clean_line, self.styles['Normal']))
                    else:
                        # Normal text
                        story.append(Paragraph(line, self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(story)
        return filename
    
    def export_to_excel(self, data, insights, filename="financial_report.xlsx"):
        """Export financial data to Excel with multiple sheets"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Main financial data
            df = data['consolidated']
            df.to_excel(writer, sheet_name='Dados Consolidados', index=False)
            
            # Summary statistics
            summary_df = pd.DataFrame([
                ['Métrica', 'Total', 'Média', 'Mínimo', 'Máximo', 'CAGR'],
                ['Receita', 
                 f"R$ {data['summary']['metrics'].get('revenue', {}).get('total', 0):,.2f}",
                 f"R$ {data['summary']['metrics'].get('revenue', {}).get('average', 0):,.2f}",
                 f"R$ {data['summary']['metrics'].get('revenue', {}).get('min', 0):,.2f}",
                 f"R$ {data['summary']['metrics'].get('revenue', {}).get('max', 0):,.2f}",
                 f"{data['summary']['metrics'].get('revenue', {}).get('cagr', 0):.1f}%"
                ]
            ])
            summary_df.to_excel(writer, sheet_name='Resumo', index=False, header=False)
            
            # Anomalies if any
            if data.get('anomalies'):
                anomalies_df = pd.DataFrame(data['anomalies'])
                anomalies_df.to_excel(writer, sheet_name='Anomalias', index=False)
            
            # AI Insights
            if insights:
                insights_df = pd.DataFrame([['Insights de IA'], [insights]])
                insights_df.to_excel(writer, sheet_name='Insights IA', index=False, header=False)
            
            # Format worksheets
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return filename
    
    def create_charts(self, data):
        """Create charts for export"""
        df = data['consolidated']
        charts = {}
        
        # Revenue evolution chart
        fig_revenue = go.Figure()
        fig_revenue.add_trace(go.Scatter(
            x=df['year'],
            y=df['revenue'],
            mode='lines+markers',
            name='Receita',
            line=dict(width=3, color='#2c5aa0'),
            marker=dict(size=10)
        ))
        fig_revenue.update_layout(
            title='Evolução da Receita',
            xaxis_title='Ano',
            yaxis_title='Receita (R$)',
            template='plotly_white'
        )
        
        # Save as temporary image
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        fig_revenue.write_image(temp_file.name)
        charts['revenue'] = temp_file.name
        
        return charts