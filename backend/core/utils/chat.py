import re
from django.utils import timezone
from datetime import timedelta

def get_ban_duration(violation_count):
    # 1h, 3h, 5h, 12h, 24h, 48h, 1w (168h), 1m (720h), 1y (8760h), 10y (87600h)
    durations = [1, 3, 5, 12, 24, 48, 168, 720, 8760, 87600]
    index = min(violation_count - 1, len(durations) - 1)
    return durations[index]

def handle_violation(user, description):
    from ..models import Violation
    from django.utils import timezone
    from datetime import timedelta
    
    # Create the violation record first
    Violation.objects.create(user=user, description=description)
    
    # Check violations in the last 7 days
    one_week_ago = timezone.now() - timedelta(days=7)
    recent_violations_count = Violation.objects.filter(user=user, created_at__gte=one_week_ago).count()
    
    if recent_violations_count >= 3:
        user.is_suspended = True
        user.save()
        return "Account suspended due to repeated violations (3+ in a week). Please contact admin for unblocking."
    else:
        user.violation_count += 1
        duration_hours = get_ban_duration(user.violation_count)
        user.ban_until = timezone.now() + timedelta(hours=duration_hours)
        user.save()
        return f"Contact information detected. Account restricted for {duration_hours}h."

def filter_chat_message(content, user, project=None):
    import re
    if not content:
        return content, False
        
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b'
    link_pattern = r'facebook\.com|instagram\.com|linkedin\.com|twitter\.com|t\.me|wa\.me|bit\.ly'
    
    has_violation = False
    if re.search(email_pattern, content, re.IGNORECASE):
        has_violation = True
    if not has_violation and re.search(phone_pattern, content):
        has_violation = True
    if not has_violation and re.search(link_pattern, content, re.IGNORECASE):
        has_violation = True
    
    if not has_violation:
        digits_only = re.sub(r'\D', '', content)
        if 10 <= len(digits_only) <= 15:
            has_violation = True

    if has_violation:
        msg = handle_violation(user, f"Contact info shared in text: {content[:50]}...")
        content = re.sub(email_pattern, '[EMAIL REDACTED]', content, flags=re.IGNORECASE)
        content = re.sub(phone_pattern, '[PHONE REDACTED]', content)
        content = re.sub(link_pattern, '[LINK REDACTED]', content, flags=re.IGNORECASE)
        if has_violation and not (re.search(email_pattern, content) or re.search(phone_pattern, content)):
             content = "[CONTENT REDACTED]"

    return content, has_violation

def scan_image_for_violations(image_file, user):
    if not image_file:
        return False
    try:
        from PIL import Image
        import pytesseract
        import re
        image_file.seek(0)
        img = Image.open(image_file)
        text = pytesseract.image_to_string(img)
        
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b'
        
        if re.search(email_pattern, text, re.IGNORECASE) or re.search(phone_pattern, text):
            handle_violation(user, "Contact info shared in MEDIA.")
            return True
    except Exception:
        pass
    finally:
        try:
            image_file.seek(0)
        except Exception:
            pass
    return False
