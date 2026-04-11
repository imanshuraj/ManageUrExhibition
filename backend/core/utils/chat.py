import re
def filter_chat_message(content, user):
    from ..models import Violation
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    has_violation = False
    if re.search(email_pattern, content) or re.search(phone_pattern, content):
        has_violation = True
    if has_violation:
        Violation.objects.create(
            user=user,
            description=f"Attempted to share contact info in message: {content[:50]}..."
        )
        content = re.sub(email_pattern, '[EMAIL REDACTED]', content)
        content = re.sub(phone_pattern, '[PHONE REDACTED]', content)
    return content, has_violation

def scan_image_for_violations(image_file, user):
    return False
