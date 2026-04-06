"""
PDF exporter for analytics dashboards.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)


class AnalyticsPDFExporter:
    """Generate analytics summary PDF."""

    def __init__(self, user, overview, details, report_type='Company'):
        self.user = user
        self.overview = overview or {}
        self.details = details or {}
        self.report_type = report_type
        self.buffer = io.BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            name='Heading',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            textColor=colors.HexColor('#111827')
        ))
        self.styles.add(ParagraphStyle(
            name='SubHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor('#374151')
        ))

    def generate(self):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )
        story = []

        title = f"{self.report_type} Analytics · Generated {datetime.now():%b %d, %Y}"
        story.append(Paragraph(title, self.styles['Heading']))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Overview", self.styles['SubHeading']))
        story.append(self._build_overview_table())
        story.append(Spacer(1, 0.2 * inch))

        if self.details.get('source_breakdown'):
            story.append(Paragraph("Applicant Sources", self.styles['SubHeading']))
            story.append(self._build_source_table())
            story.append(Spacer(1, 0.2 * inch))

        if self.details.get('top_skills'):
            story.append(Paragraph("Top Skills", self.styles['SubHeading']))
            story.append(self._build_skill_table('top_skills'))
            story.append(Spacer(1, 0.2 * inch))

        if self.details.get('skill_gaps'):
            story.append(Paragraph("Skill Gaps", self.styles['SubHeading']))
            story.append(self._build_skill_table('skill_gaps'))
            story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        self.buffer.seek(0)
        return self.buffer

    def _build_overview_table(self):
        headers = [['Metric', 'Value']]
        rows = []
        for label, key in [
            ('Total Applications', 'total_applications'),
            ('Total Hires', 'total_hires'),
            ('Avg Time to Hire (days)', 'avg_time_to_hire'),
            ('Cost per Hire', 'cost_per_hire'),
            ('Success Rate (%)', 'success_rate'),
            ('Avg Match Score', 'avg_match_score'),
        ]:
            value = self.overview.get(key)
            if value is None:
                continue
            if isinstance(value, float):
                value = f"{value:.1f}"
            rows.append([label, str(value)])

        table = Table(headers + rows, colWidths=[3 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111827')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        return table

    def _build_source_table(self):
        rows = [['Source', 'Count']]
        for source, count in self.details.get('source_breakdown', {}).items():
            rows.append([source.capitalize(), str(count)])
        table = Table(rows, colWidths=[3 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1d4ed8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1d4ed8')),
        ]))
        return table

    def _build_skill_table(self, field):
        rows = [['Skill', 'Count']]
        for item in self.details.get(field, []):
            rows.append([item.get('skill', 'Unknown'), str(item.get('count', 0))])
        table = Table(rows, colWidths=[3 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#059669')),
        ]))
        return table
