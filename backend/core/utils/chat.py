import re
from django.utils import timezone
from datetime import timedelta

def get_ban_duration(violation_count):
    # 1h, 3h, 5h, 12h, 24h, 48h, 1w (168h), 1m (720h), 1y (8760h), 10y (87600h)
    durations = [1, 3, 5, 12, 24, 48, 168, 720, 8760, 87600]
    index = min(violation_count - 1, len(durations) - 1)
    return durations[index]

def filter_chat_message(content, user, project=None):
    from ..models import Violation
    
    # Don't filter if project is paid
    if project and project.is_paid:
        return content, False
        
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    
    has_violation = False
    if re.search(email_pattern, content) or re.search(phone_pattern, content):
        has_violation = True
        
    if has_violation:
        user.violation_count += 1
        duration_hours = get_ban_duration(user.violation_count)
        user.ban_until = timezone.now() + timedelta(hours=duration_hours)
        user.save()
        
        Violation.objects.create(
            user=user,
            description=f"Direct contact info shared. Banned for {duration_hours}h. Content: {content[:50]}..."
        )
        content = re.sub(email_pattern, '[EMAIL REDACTED]', content)
        content = re.sub(phone_pattern, '[PHONE REDACTED]', content)
        
    return content, has_violation

def scan_image_for_violations(image_file, user):
    # Placeholder for OCR logic
    # In a real implementation, you would use pytesseract or a cloud vision API
    return False
