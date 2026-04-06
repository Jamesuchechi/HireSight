"""
Django management command to load initial resume templates
Usage: python manage.py load_resume_templates
"""

from django.core.management.base import BaseCommand
from apps.resumes.models import ResumeTemplate


class Command(BaseCommand):
    help = 'Load 10 initial professional resume templates'

    def handle(self, *args, **options):
        self.stdout.write('Loading resume templates...')
        
        templates_data = [
            {
                'name': 'Modern Professional',
                'slug': 'modern-professional',
                'description': 'Clean, contemporary design perfect for tech and creative industries. Features bold headers and a minimalist aesthetic.',
                'category': 'modern',
                'tone': 'professional',
                'html_template': self.get_modern_html(),
                'css_styles': self.get_modern_css(),
                'writing_style_guide': 'Use concise, impactful language. Emphasize achievements with metrics. Start bullet points with strong action verbs. Keep sentences short and punchy.',
                'section_priorities': {
                    'summary': 10,
                    'experience': 9,
                    'skills': 8,
                    'education': 7,
                    'certifications': 6
                },
                'default_color_scheme': {
                    'primary': '#2563eb',
                    'secondary': '#64748b',
                    'accent': '#0ea5e9',
                    'text': '#1e293b'
                },
                'is_active': True,
                'is_premium': False
            },
            {
                'name': 'Classic Executive',
                'slug': 'classic-executive',
                'description': 'Traditional, elegant layout ideal for senior positions and conservative industries like finance and law.',
                'category': 'classic',
                'tone': 'professional',
                'html_template': self.get_classic_html(),
                'css_styles': self.get_classic_css(),
                'writing_style_guide': 'Use formal, traditional language. Focus on leadership and strategic achievements. Emphasize experience and credentials. Use complete sentences.',
                'section_priorities': {
                    'experience': 10,
                    'education': 9,
                    'summary': 8,
                    'skills': 7,
                    'certifications': 8
                },
                'default_color_scheme': {
                    'primary': '#1f2937',
                    'secondary': '#6b7280',
                    'accent': '#374151',
                    'text': '#111827'
                },
                'is_active': True,
                'is_premium': False
            },
            {
                'name': 'ATS Optimized',
                'slug': 'ats-optimized',
                'description': 'Designed to pass Applicant Tracking Systems with simple formatting and keyword-friendly structure.',
                'category': 'ats',
                'tone': 'professional',
                'html_template': self.get_ats_html(),
                'css_styles': self.get_ats_css(),
                'writing_style_guide': 'Use industry-standard keywords. Include relevant technical terms. Use clear section headers. Optimize for ATS parsing with simple formatting.',
                'section_priorities': {
                    'skills': 10,
                    'experience': 9,
                    'education': 8,
                    'certifications': 8,
                    'summary': 7
                },
                'default_color_scheme': {
                    'primary': '#000000',
                    'secondary': '#4b5563',
                    'accent': '#1f2937',
                    'text': '#000000'
                },
                'is_active': True,
                'is_premium': False
            },
            {
                'name': 'Creative Portfolio',
                'slug': 'creative-portfolio',
                'description': 'Bold, eye-catching design for designers, artists, and creative professionals.',
                'category': 'creative',
                'tone': 'friendly',
                'html_template': self.get_creative_html(),
                'css_styles': self.get_creative_css(),
                'writing_style_guide': 'Use creative, engaging language. Showcase personality and unique voice. Emphasize projects and portfolio work. Be descriptive and vivid.',
                'section_priorities': {
                    'portfolio': 10,
                    'experience': 9,
                    'skills': 8,
                    'summary': 8,
                    'education': 6
                },
                'default_color_scheme': {
                    'primary': '#8b5cf6',
                    'secondary': '#ec4899',
                    'accent': '#f59e0b',
                    'text': '#1e293b'
                },
                'is_active': True,
                'is_premium': True
            },
            {
                'name': 'Tech Minimalist',
                'slug': 'tech-minimalist',
                'description': 'Ultra-clean design for software engineers and tech professionals. Focuses on skills and projects.',
                'category': 'tech',
                'tone': 'professional',
                'html_template': self.get_tech_html(),
                'css_styles': self.get_tech_css(),
                'writing_style_guide': 'Use technical terminology accurately. Emphasize technologies and frameworks. Highlight open-source contributions. Be precise and specific.',
                'section_priorities': {
                    'skills': 10,
                    'projects': 9,
                    'experience': 9,
                    'education': 7,
                    'summary': 6
                },
                'default_color_scheme': {
                    'primary': '#10b981',
                    'secondary': '#6b7280',
                    'accent': '#059669',
                    'text': '#111827'
                },
                'is_active': True,
                'is_premium': False
            },
            {
                'name': 'Academic Scholar',
                'slug': 'academic-scholar',
                'description': 'Comprehensive format for academics, researchers, and educators. Emphasizes publications and research.',
                'category': 'academic',
                'tone': 'authoritative',
                'html_template': self.get_academic_html(),
                'css_styles': self.get_academic_css(),
                'writing_style_guide': 'Use scholarly, precise language. Emphasize research, publications, and academic achievements. Include citations and references. Be thorough and detailed.',
                'section_priorities': {
                    'education': 10,
                    'publications': 10,
                    'research': 9,
                    'experience': 8,
                    'skills': 6
                },
                'default_color_scheme': {
                    'primary': '#1e40af',
                    'secondary': '#64748b',
                    'accent': '#3b82f6',
                    'text': '#0f172a'
                },
                'is_active': True,
                'is_premium': False
            },
            {
                'name': 'Sales Dynamo',
                'slug': 'sales-dynamo',
                'description': 'Results-focused template for sales professionals. Highlights achievements and metrics.',
                'category': 'sales',
                'tone': 'confident',
                'html_template': self.get_sales_html(),
                'css_styles': self.get_sales_css(),
                'writing_style_guide': 'Use confident, results-oriented language. Lead with numbers and achievements. Emphasize revenue growth and targets exceeded. Be persuasive and energetic.',
                'section_priorities': {
                    'achievements': 10,
                    'experience': 9,
                    'skills': 7,
                    'summary': 8,
                    'education': 6
                },
                'default_color_scheme': {
                    'primary': '#dc2626',
                    'secondary': '#64748b',
                    'accent': '#ef4444',
                    'text': '#1e293b'
                },
                'is_active': True,
                'is_premium': False
            },
            {
                'name': 'Healthcare Professional',
                'slug': 'healthcare-professional',
                'description': 'Clean, trustworthy design for medical and healthcare professionals.',
                'category': 'healthcare',
                'tone': 'professional',
                'html_template': self.get_healthcare_html(),
                'css_styles': self.get_healthcare_css(),
                'writing_style_guide': 'Use professional medical terminology. Emphasize certifications and patient care. Highlight clinical experience. Be clear and compassionate.',
                'section_priorities': {
                    'certifications': 10,
                    'experience': 9,
                    'education': 9,
                    'skills': 8,
                    'summary': 7
                },
                'default_color_scheme': {
                    'primary': '#0891b2',
                    'secondary': '#64748b',
                    'accent': '#06b6d4',
                    'text': '#0f172a'
                },
                'is_active': True,
                'is_premium': False
            },
            {
                'name': 'Startup Innovator',
                'slug': 'startup-innovator',
                'description': 'Dynamic template for entrepreneurs and startup professionals. Emphasizes innovation and impact.',
                'category': 'startup',
                'tone': 'enthusiastic',
                'html_template': self.get_startup_html(),
                'css_styles': self.get_startup_css(),
                'writing_style_guide': 'Use dynamic, innovative language. Emphasize impact and growth. Highlight entrepreneurial achievements. Be bold and forward-thinking.',
                'section_priorities': {
                    'achievements': 10,
                    'experience': 9,
                    'skills': 8,
                    'summary': 9,
                    'education': 6
                },
                'default_color_scheme': {
                    'primary': '#f59e0b',
                    'secondary': '#64748b',
                    'accent': '#fbbf24',
                    'text': '#1e293b'
                },
                'is_active': True,
                'is_premium': True
            },
            {
                'name': 'International Executive',
                'slug': 'international-executive',
                'description': 'Sophisticated template for global leaders and international business professionals.',
                'category': 'executive',
                'tone': 'authoritative',
                'html_template': self.get_executive_html(),
                'css_styles': self.get_executive_css(),
                'writing_style_guide': 'Use sophisticated, global business language. Emphasize international experience and leadership. Highlight strategic achievements. Be authoritative and polished.',
                'section_priorities': {
                    'summary': 10,
                    'experience': 10,
                    'achievements': 9,
                    'education': 8,
                    'skills': 7
                },
                'default_color_scheme': {
                    'primary': '#4338ca',
                    'secondary': '#64748b',
                    'accent': '#6366f1',
                    'text': '#0f172a'
                },
                'is_active': True,
                'is_premium': True
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates_data:
            template, created = ResumeTemplate.objects.update_or_create(
                slug=template_data['slug'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {template.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ Updated: {template.name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Done! Created {created_count} templates, updated {updated_count} templates.'
        ))
    
    # HTML Templates (simplified for initial load)
    def get_modern_html(self):
        return '''
        <div class="resume">
            <header class="header">
                <h1>{{ contact.name }}</h1>
                <div class="contact-info">
                    <span>{{ contact.email }}</span>
                    <span>{{ contact.phone }}</span>
                    <span>{{ contact.location }}</span>
                </div>
            </header>
            
            {% if summary %}
            <section class="summary">
                <h2>Professional Summary</h2>
                <p>{{ summary }}</p>
            </section>
            {% endif %}
            
            <section class="experience">
                <h2>Experience</h2>
                {% for job in experience %}
                <div class="job">
                    <h3>{{ job.title }}</h3>
                    <div class="company">{{ job.company }} | {{ job.dates }}</div>
                    <ul>
                        {% for item in job.responsibilities %}
                        <li>{{ item }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endfor %}
            </section>
            
            <section class="skills">
                <h2>Skills</h2>
                <div class="skills-list">
                    {% for skill in skills %}
                    <span class="skill">{{ skill }}</span>
                    {% endfor %}
                </div>
            </section>
            
            <section class="education">
                <h2>Education</h2>
                {% for edu in education %}
                <div class="degree">
                    <h3>{{ edu.degree }}</h3>
                    <div>{{ edu.institution }} | {{ edu.year }}</div>
                </div>
                {% endfor %}
            </section>
        </div>
        '''
    
    def get_modern_css(self):
        return '''
        .resume { font-family: 'Inter', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 3px solid {{ primary }}; padding-bottom: 20px; }
        .header h1 { color: {{ primary }}; font-size: 36px; margin: 0; }
        .contact-info { margin-top: 10px; color: {{ secondary }}; }
        .contact-info span { margin: 0 10px; }
        section { margin-bottom: 30px; }
        h2 { color: {{ primary }}; font-size: 24px; border-bottom: 2px solid {{ accent }}; padding-bottom: 5px; }
        .job { margin-bottom: 20px; }
        .job h3 { color: {{ text }}; margin-bottom: 5px; }
        .company { color: {{ secondary }}; font-style: italic; margin-bottom: 10px; }
        ul { margin: 10px 0; padding-left: 20px; }
        .skills-list { display: flex; flex-wrap: wrap; gap: 10px; }
        .skill { background: {{ accent }}; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; }
        '''
    
    # Simplified templates for other categories (using similar structure)
    def get_classic_html(self):
        return self.get_modern_html()  # Reuse structure
    
    def get_classic_css(self):
        return '''
        .resume { font-family: 'Georgia', serif; max-width: 800px; margin: 0 auto; padding: 40px; }
        .header { margin-bottom: 30px; border-bottom: 2px solid {{ primary }}; padding-bottom: 15px; }
        .header h1 { color: {{ primary }}; font-size: 32px; margin: 0; }
        .contact-info { margin-top: 10px; color: {{ secondary }}; }
        section { margin-bottom: 25px; }
        h2 { color: {{ primary }}; font-size: 20px; border-bottom: 1px solid {{ secondary }}; padding-bottom: 5px; }
        '''
    
    def get_ats_html(self):
        return self.get_modern_html()
    
    def get_ats_css(self):
        return '''
        .resume { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header h1 { font-size: 28px; margin: 0; }
        h2 { font-size: 18px; margin-top: 20px; margin-bottom: 10px; }
        ul { margin: 5px 0; padding-left: 20px; }
        '''
    
    def get_creative_html(self):
        return self.get_modern_html()
    
    def get_creative_css(self):
        return self.get_modern_css()
    
    def get_tech_html(self):
        return self.get_modern_html()
    
    def get_tech_css(self):
        return self.get_modern_css()
    
    def get_academic_html(self):
        return self.get_modern_html()
    
    def get_academic_css(self):
        return self.get_modern_css()
    
    def get_sales_html(self):
        return self.get_modern_html()
    
    def get_sales_css(self):
        return self.get_modern_css()
    
    def get_healthcare_html(self):
        return self.get_modern_html()
    
    def get_healthcare_css(self):
        return self.get_modern_css()
    
    def get_startup_html(self):
        return self.get_modern_html()
    
    def get_startup_css(self):
        return self.get_modern_css()
    
    def get_executive_html(self):
        return self.get_modern_html()
    
    def get_executive_css(self):
        return self.get_modern_css()
