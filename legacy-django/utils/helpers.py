import markdown
import bleach


def convert_markdown_to_html(text: str) -> str:
    """
    Convert markdown text to HTML and sanitize the result for safe rendering.
    """
    if not text:
        return ""

    html = markdown.markdown(
        text,
        extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists']
    )

    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'span', 'div'
    ]
    allowed_attributes = {
        'a': ['href', 'title', 'rel', 'target'],
        'span': ['class'],
        'div': ['class']
    }

    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )

    return clean_html
