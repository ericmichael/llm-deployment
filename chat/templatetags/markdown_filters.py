from django import template
from bs4 import BeautifulSoup
import markdown

register = template.Library()

@register.filter
def markdown_to_html(md_string):
    html = markdown.markdown(md_string, extensions=['fenced_code'])
    return html

@register.filter
@register.filter
def enhance_markdown_html(html_string, default_language=None):
    soup = BeautifulSoup(html_string, 'html.parser')
    block_elements = soup.find_all(['p', 'pre', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'hr', 'li'])

    # Only add margin if there are multiple block elements
    if len(block_elements) > 1:
        for element in block_elements[:-1]:  # Exclude the last element
            element['class'] = element.get('class', []) + ['mb-4']  # Add bottom margin

    for code_tag in soup.find_all('code'):
        if not code_tag.has_attr('class') and default_language is not None:
            code_tag['class'] = f'language-{default_language}'

    return str(soup)