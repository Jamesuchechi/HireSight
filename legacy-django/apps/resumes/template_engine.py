"""
Resume template rendering engine
Handles template selection, customization, and rendering
"""

import logging
from typing import Dict, Any, Optional
from jinja2 import Template, Environment, select_autoescape

logger = logging.getLogger(__name__)


class ResumeTemplateRenderer:
    """Renders resume content using selected template"""
    
    def __init__(self, template_obj, customization=None):
        """
        Initialize renderer with template and optional customization
        
        Args:
            template_obj: ResumeTemplate instance
            customization: ResumeTemplateCustomization instance (optional)
        """
        self.template = template_obj
        self.customization = customization
        self.env = Environment(autoescape=select_autoescape(['html', 'xml']))
    
    def render_html(self, resume_data: Dict[str, Any]) -> str:
        """
        Render resume as HTML using template
        
        Args:
            resume_data: Dictionary containing resume information
            
        Returns:
            Rendered HTML string
        """
        try:
            # Merge template defaults with customizations
            context = self._build_context(resume_data)
            
            # Render template
            jinja_template = self.env.from_string(self.template.html_template)
            html_content = jinja_template.render(**context)
            
            logger.info(f"Successfully rendered template: {self.template.name}")
            return html_content
            
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise
    
    def render_with_css(self, resume_data: Dict[str, Any]) -> tuple[str, str]:
        """
        Render resume HTML and CSS separately
        
        Args:
            resume_data: Dictionary containing resume information
            
        Returns:
            Tuple of (html_content, css_content)
        """
        html = self.render_html(resume_data)
        css = self._get_compiled_css()
        return html, css
    
    def _build_context(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build template context with data and customizations
        
        Args:
            resume_data: Resume information dictionary
            
        Returns:
            Complete context dictionary for template rendering
        """
        context = {
            'resume': resume_data,
            'template': self.template,
            'colors': self._get_colors(),
            'fonts': self._get_fonts(),
            'sections': self._get_section_config(),
            'layout': self._get_layout_settings(),
        }
        return context
    
    def _get_colors(self) -> Dict[str, str]:
        """
        Get color scheme (custom or default)
        
        Returns:
            Dictionary of color values
        """
        default_colors = self.template.default_color_scheme or {
            'primary': '#2563eb',
            'secondary': '#64748b',
            'accent': '#f59e0b',
            'text': '#1f2937',
            'background': '#ffffff',
        }
        
        if self.customization and self.customization.color_scheme:
            return {**default_colors, **self.customization.color_scheme}
        
        return default_colors
    
    def _get_fonts(self) -> Dict[str, Any]:
        """
        Get font settings
        
        Returns:
            Dictionary of font configuration
        """
        default_fonts = {
            'heading': 'Inter',
            'body': 'Open Sans',
            'size': 11,
            'line_height': 1.5,
        }
        
        if self.customization and self.customization.font_settings:
            return {**default_fonts, **self.customization.font_settings}
        
        return default_fonts
    
    def _get_section_config(self) -> Dict[str, Any]:
        """
        Get section order and visibility
        
        Returns:
            Dictionary with section configuration
        """
        default_order = [
            'summary',
            'experience',
            'education',
            'skills',
            'certifications',
            'projects',
        ]
        default_visibility = {section: True for section in default_order}
        
        if self.customization:
            order = self.customization.section_order or default_order
            visibility = {
                **default_visibility,
                **(self.customization.section_visibility or {})
            }
            return {'order': order, 'visibility': visibility}
        
        return {'order': default_order, 'visibility': default_visibility}
    
    def _get_layout_settings(self) -> Dict[str, Any]:
        """
        Get layout configuration
        
        Returns:
            Dictionary of layout settings
        """
        default_layout = {
            'margins': '0.75in',
            'columns': 1,
            'spacing': 'normal',
            'page_size': 'letter',
        }
        
        if self.customization and self.customization.layout_settings:
            return {**default_layout, **self.customization.layout_settings}
        
        return default_layout
    
    def _get_compiled_css(self) -> str:
        """
        Get compiled CSS with customizations applied
        
        Returns:
            CSS string with variables replaced
        """
        css = self.template.css_styles
        colors = self._get_colors()
        fonts = self._get_fonts()
        layout = self._get_layout_settings()
        
        # Replace CSS variables
        replacements = {
            '--color-primary': colors.get('primary', '#2563eb'),
            '--color-secondary': colors.get('secondary', '#64748b'),
            '--color-accent': colors.get('accent', '#f59e0b'),
            '--color-text': colors.get('text', '#1f2937'),
            '--color-background': colors.get('background', '#ffffff'),
            '--font-heading': fonts.get('heading', 'Inter'),
            '--font-body': fonts.get('body', 'Open Sans'),
            '--font-size': f"{fonts.get('size', 11)}pt",
            '--line-height': str(fonts.get('line_height', 1.5)),
            '--margin': layout.get('margins', '0.75in'),
        }
        
        for var, value in replacements.items():
            css = css.replace(var, value)
        
        return css


class TemplateValidator:
    """Validate template HTML and CSS before saving"""
    
    @staticmethod
    def validate_html(html_template: str) -> tuple[bool, Optional[str]]:
        """
        Validate HTML template syntax
        
        Args:
            html_template: Jinja2 template string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            env = Environment(autoescape=select_autoescape(['html', 'xml']))
            env.from_string(html_template)
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def validate_css(css_styles: str) -> tuple[bool, Optional[str]]:
        """
        Validate CSS syntax (basic check)
        
        Args:
            css_styles: CSS string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation - check for balanced braces
        if css_styles.count('{') != css_styles.count('}'):
            return False, "Unbalanced braces in CSS"
        
        return True, None
    
    @staticmethod
    def validate_template(template_obj) -> tuple[bool, list[str]]:
        """
        Validate complete template
        
        Args:
            template_obj: ResumeTemplate instance
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate HTML
        html_valid, html_error = TemplateValidator.validate_html(
            template_obj.html_template
        )
        if not html_valid:
            errors.append(f"HTML Error: {html_error}")
        
        # Validate CSS
        css_valid, css_error = TemplateValidator.validate_css(
            template_obj.css_styles
        )
        if not css_valid:
            errors.append(f"CSS Error: {css_error}")
        
        # Check required fields
        if not template_obj.name:
            errors.append("Template name is required")
        if not template_obj.slug:
            errors.append("Template slug is required")
        
        return len(errors) == 0, errors
