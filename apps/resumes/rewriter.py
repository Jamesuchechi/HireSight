from .optimization import MistralResumeAdvisor


class ResumeRewriter:
    """Wrapper around the AI advisor for full resume rewrites."""

    def __init__(self):
        self.ai_advisor = MistralResumeAdvisor()

    def rewrite_resume(self, resume_text: str, job_title: str = '', industry: str = '',
                       highlights: str = '', metrics_focus: str = '', job_description: str = '',
                       header_text: str = None):
        """
        Generate a rewritten resume provided the original text and optional context.
        """
        return self.ai_advisor.generate_rewrite(
            resume_text,
            job_title=job_title,
            industry=industry,
            highlights=highlights,
            metrics_focus=metrics_focus,
            job_description=job_description,
            header_text=header_text
        )
