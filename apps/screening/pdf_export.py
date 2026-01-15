"""
PDF Export utilities for screening results.
Generates comprehensive PDF reports with charts and candidate details.
"""
import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.db.models import Avg, Count, Q

logger = logging.getLogger(__name__)


class ScreeningPDFExporter:
    """Generate PDF reports for screening sessions."""
    
    def __init__(self, session, results=None):
        """Initialize PDF exporter."""
        self.session = session
        if results is None:
            self.results = session.results.filter(
                status='completed'
            ).order_by('-match_score')
        else:
            # Convert results to list if it's a QuerySet for easier handling
            self.results = list(results) if hasattr(results, '__iter__') else results
        self.buffer = io.BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#6366f1'),  # Primary color
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f2937'),  # Dark gray
            spaceAfter=6,
            spaceBefore=6,
            fontName='Helvetica-Bold'
        ))
        
        # Normal style
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),  # Gray
            spaceAfter=6
        ))
        
        # Table header style
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        # Table cell style
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#374151'),
            alignment=TA_LEFT
        ))
    
    def generate(self):
        """Generate the complete PDF report."""
        try:
            doc = SimpleDocTemplate(
                self.buffer,
                pagesize=letter,
                rightMargin=0.5 * inch,
                leftMargin=0.5 * inch,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch
            )
            
            # Build PDF content
            story = []
            
            # Add title page
            story.extend(self._build_title_page())
            
            # Add executive summary
            story.append(PageBreak())
            story.extend(self._build_executive_summary())
            
            # Add analytics charts/data
            story.append(PageBreak())
            story.extend(self._build_analytics_section())
            
            # Add top candidates
            story.append(PageBreak())
            story.extend(self._build_top_candidates_section())
            
            # Add detailed results
            story.append(PageBreak())
            story.extend(self._build_detailed_results_section())
            
            # Build PDF
            doc.build(story)
            
            self.buffer.seek(0)
            logger.info(f"PDF generated successfully for session {self.session.id}")
            return self.buffer
        
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
            raise
    
    def _build_title_page(self):
        """Build title page."""
        story = []
        
        # Spacer
        story.append(Spacer(1, 1.5 * inch))
        
        # Title
        title = Paragraph(
            "Screening Results Report",
            self.styles['CustomTitle']
        )
        story.append(title)
        
        # Session info
        session_info = f"<b>{self.session.title}</b><br/>"
        if self.session.job:
            session_info += f"Job: {self.session.job.title}<br/>"
        session_info += f"Generated: {datetime.now().strftime('%B %d, %Y')}<br/>"
        session_info += f"Company: {self.session.company.name}"
        
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(session_info, self.styles['CustomNormal']))
        
        # Statistics boxes
        story.append(Spacer(1, 0.5 * inch))
        story.extend(self._build_stat_boxes())
        
        return story
    
    def _build_stat_boxes(self):
        """Build statistics boxes for title page."""
        total = len(self.results)
        excellent = sum(1 for r in self.results if r.match_score >= 90)
        strong = sum(1 for r in self.results if 80 <= r.match_score < 90)
        good = sum(1 for r in self.results if 70 <= r.match_score < 80)
        shortlisted = sum(1 for r in self.results if r.is_shortlisted)
        avg_score = sum(r.match_score for r in self.results) / total if total > 0 else 0
        
        # Create table data
        data = [
            [
                f"<b>Total<br/>Candidates</b><br/>{total}",
                f"<b>Average<br/>Score</b><br/>{avg_score:.1f}%",
                f"<b>Shortlisted</b><br/>{shortlisted}"
            ],
            [
                f"<b>Excellent<br/>(90+)</b><br/>{excellent}",
                f"<b>Strong<br/>(80-89)</b><br/>{strong}",
                f"<b>Good<br/>(70-79)</b><br/>{good}"
            ]
        ]
        
        # Create table
        table = Table(data, colWidths=[2 * inch, 2 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
        ]))
        
        return [table]
    
    def _build_executive_summary(self):
        """Build executive summary section."""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Calculate summary statistics
        total = len(self.results)
        avg_score = sum(r.match_score for r in self.results) / total if total > 0 else 0
        shortlisted = sum(1 for r in self.results if r.is_shortlisted)
        shortlist_pct = (shortlisted / total * 100) if total > 0 else 0
        high_score_count = sum(1 for r in self.results if r.match_score >= 80)
        low_score_count = sum(1 for r in self.results if r.match_score < 50)
        top_score = self.results[0].match_score if self.results else 'N/A'
        
        summary_text = f"""
        <b>Screening Overview:</b><br/>
        A total of {total} candidates were screened against the job requirements for {self.session.title}.
        The screening process identified an average match score of {avg_score:.1f}%, with {shortlisted} 
        candidate(s) ({shortlist_pct:.1f}%) recommended for further consideration.<br/>
        <br/>
        <b>Key Findings:</b><br/>
        • {high_score_count} candidates scored 80% or higher<br/>
        • {low_score_count} candidates scored below 50%<br/>
        • Top candidate match score: {top_score}%<br/>
        """
        
        story.append(Paragraph(summary_text, self.styles['CustomNormal']))
        
        return story
    
    def _build_analytics_section(self):
        """Build analytics and statistics section."""
        story = []
        
        story.append(Paragraph("Screening Analytics", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Score distribution
        score_dist = self._calculate_score_distribution()
        story.extend(self._build_score_distribution_table(score_dist))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # Experience distribution
        exp_dist = self._calculate_experience_distribution()
        story.extend(self._build_experience_distribution_table(exp_dist))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # Top skills
        top_skills = self._calculate_top_skills()
        story.extend(self._build_top_skills_table(top_skills))
        
        return story
    
    def _calculate_score_distribution(self):
        """Calculate score distribution."""
        return {
            '90-100': sum(1 for r in self.results if r.match_score >= 90),
            '80-89': sum(1 for r in self.results if 80 <= r.match_score < 90),
            '70-79': sum(1 for r in self.results if 70 <= r.match_score < 80),
            '60-69': sum(1 for r in self.results if 60 <= r.match_score < 70),
            '0-59': sum(1 for r in self.results if r.match_score < 60),
        }
    
    def _build_score_distribution_table(self, dist):
        """Build score distribution table."""
        story = []
        
        story.append(Paragraph("<b>Match Score Distribution</b>", self.styles['CustomNormal']))
        story.append(Spacer(1, 0.1 * inch))
        
        # Create distribution table
        data = [['Score Range', 'Count', 'Percentage']]
        total = sum(dist.values())
        
        for range_name, count in dist.items():
            pct = (count / total * 100) if total > 0 else 0
            # Create visual bar
            bar_width = int(pct / 5)  # Max 20 chars = 100%
            bar = '█' * bar_width
            data.append([range_name, str(count), f"{pct:.1f}% {bar}"])
        
        table = Table(data, colWidths=[1.5 * inch, 1 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        return story
    
    def _calculate_experience_distribution(self):
        """Calculate experience distribution."""
        exp_ranges = {
            '0-2 years': 0,
            '2-4 years': 0,
            '4-6 years': 0,
            '6-8 years': 0,
            '8+ years': 0,
        }
        
        for result in self.results:
            exp_match = result.match_details.get('experience_match', {})
            if isinstance(exp_match, dict) and 'years' in exp_match:
                years = exp_match['years']
                if years < 2:
                    exp_ranges['0-2 years'] += 1
                elif years < 4:
                    exp_ranges['2-4 years'] += 1
                elif years < 6:
                    exp_ranges['4-6 years'] += 1
                elif years < 8:
                    exp_ranges['6-8 years'] += 1
                else:
                    exp_ranges['8+ years'] += 1
        
        return exp_ranges
    
    def _build_experience_distribution_table(self, dist):
        """Build experience distribution table."""
        story = []
        
        story.append(Paragraph("<b>Experience Distribution</b>", self.styles['CustomNormal']))
        story.append(Spacer(1, 0.1 * inch))
        
        data = [['Experience Level', 'Count']]
        total = sum(dist.values())
        
        for exp_range, count in dist.items():
            pct = (count / total * 100) if total > 0 else 0
            bar_width = int(pct / 5)
            bar = '█' * bar_width
            data.append([exp_range, f"{count} ({pct:.1f}%) {bar}"])
        
        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        return story
    
    def _calculate_top_skills(self, limit=8):
        """Calculate top matched skills."""
        skills_count = {}
        
        for result in self.results:
            matched_skills = result.match_details.get('skills_match', {}).get('matched', [])
            for skill in matched_skills:
                skills_count[skill] = skills_count.get(skill, 0) + 1
        
        # Sort and limit
        sorted_skills = sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        return sorted_skills
    
    def _build_top_skills_table(self, skills):
        """Build top skills table."""
        story = []
        
        story.append(Paragraph("<b>Top Matched Skills</b>", self.styles['CustomNormal']))
        story.append(Spacer(1, 0.1 * inch))
        
        if not skills:
            story.append(Paragraph("No skills data available", self.styles['CustomNormal']))
            return story
        
        data = [['Skill', 'Matched Count']]
        total_matches = sum(count for _, count in skills)
        
        for skill, count in skills:
            pct = (count / total_matches * 100) if total_matches > 0 else 0
            bar_width = int(pct / 5)
            bar = '█' * bar_width
            data.append([skill, f"{count} ({pct:.1f}%) {bar}"])
        
        table = Table(data, colWidths=[2.5 * inch, 3.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        return story
    
    def _build_top_candidates_section(self):
        """Build top candidates section."""
        story = []
        
        story.append(Paragraph("Top 10 Candidates", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2 * inch))
        
        top_candidates = self.results[:10]
        
        if not top_candidates:
            story.append(Paragraph("No candidates found", self.styles['CustomNormal']))
            return story
        
        # Create candidates table
        data = [['Rank', 'Candidate', 'Score', 'Experience', 'Status']]
        
        for idx, result in enumerate(top_candidates, 1):
            name = result.resume.user.get_full_name() if hasattr(result, 'resume') and result.resume else 'Unknown'
            score = f"{result.match_score}%"
            exp = self._get_experience_display(result)
            status = 'Shortlisted' if result.is_shortlisted else 'Not Shortlisted'
            
            data.append([str(idx), name[:30], score, exp, status])
        
        table = Table(data, colWidths=[0.6 * inch, 2.2 * inch, 0.8 * inch, 1 * inch, 1.4 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
        ]))
        
        story.append(table)
        return story
    
    def _build_detailed_results_section(self):
        """Build detailed results section."""
        story = []
        
        story.append(Paragraph("Detailed Results", self.styles['CustomHeading']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Create detailed table
        data = [['Rank', 'Candidate', 'Email', 'Score', 'Skills Match', 'Status']]
        
        for idx, result in enumerate(self.results, 1):
            name = result.resume.user.get_full_name() if hasattr(result, 'resume') and result.resume else 'Unknown'
            email = result.resume.user.email if hasattr(result, 'resume') and result.resume else 'N/A'
            score = f"{result.match_score}%"
            
            # Get matched skills count
            matched_count = len(result.match_details.get('skills_match', {}).get('matched', []))
            total_required = len(self.session.criteria.required_skills) if hasattr(self.session, 'criteria') and self.session.criteria else 0
            skills_display = f"{matched_count}/{total_required}" if total_required else f"{matched_count}"
            
            status = 'Shortlisted' if result.is_shortlisted else 'Reviewed'
            
            data.append([
                str(idx),
                name[:25],
                email[:25] if email else 'N/A',
                score,
                skills_display,
                status
            ])
            
            # Limit to 50 rows per page
            if idx % 50 == 0 and idx < len(self.results):
                # Add table for this section
                table = self._create_detailed_table(data)
                story.append(table)
                story.append(PageBreak())
                data = [['Rank', 'Candidate', 'Email', 'Score', 'Skills Match', 'Status']]
        
        # Add final table
        if len(data) > 1:
            table = self._create_detailed_table(data)
            story.append(table)
        
        return story
    
    def _create_detailed_table(self, data):
        """Create a detailed results table."""
        table = Table(data, colWidths=[0.6 * inch, 1.8 * inch, 1.8 * inch, 0.8 * inch, 0.9 * inch, 1 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),
        ]))
        return table
    
    def _get_experience_display(self, result):
        """Get experience display text."""
        exp_match = result.match_details.get('experience_match', {})
        if isinstance(exp_match, dict) and 'years' in exp_match:
            return f"{exp_match['years']} yrs"
        return 'N/A'
