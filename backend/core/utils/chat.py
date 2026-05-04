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
    import re
    
    if not content:
        return content, False
        
    # Robust patterns
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    # Phone pattern: catches 10 digits with various separators, and country codes
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b'
    # Social media and common link patterns
    link_pattern = r'facebook\.com|instagram\.com|linkedin\.com|twitter\.com|t\.me|wa\.me|bit\.ly'
    
    has_violation = False
    
    # Check for email
    if re.search(email_pattern, content, re.IGNORECASE):
        has_violation = True
    # Check for phone
    if not has_violation and re.search(phone_pattern, content):
        has_violation = True
    # Check for links
    if not has_violation and re.search(link_pattern, content, re.IGNORECASE):
        has_violation = True
    
    # Extra check for obscured phone numbers like "9 8 7 6 5 4 3 2 1 0" or "98-76-54-32-10"
    if not has_violation:
        digits_only = re.sub(r'\D', '', content)
        if len(digits_only) >= 10:
            # We assume 10+ digits in a relatively short message or clustered together is a phone number
            # To avoid false positives on large numbers, we check if they are consecutive in digits_only
            # and if the original content length isn't disproportionately large (like a long technical spec)
            if len(digits_only) <= 15: # typical phone number range including country code
                has_violation = True

    if has_violation:
        user.violation_count += 1
        duration_hours = get_ban_duration(user.violation_count)
        user.ban_until = timezone.now() + timedelta(hours=duration_hours)
        user.save()
        
        Violation.objects.create(
            user=user,
            description=f"Direct contact info shared (Text). Banned for {duration_hours}h. Content: {content[:50]}..."
        )
        content = re.sub(email_pattern, '[EMAIL REDACTED]', content, flags=re.IGNORECASE)
        content = re.sub(phone_pattern, '[PHONE REDACTED]', content)
        content = re.sub(link_pattern, '[LINK REDACTED]', content, flags=re.IGNORECASE)
        
        # If it was caught by digits_only check but not by regex, we should still redact it
        if has_violation and not (re.search(email_pattern, content) or re.search(phone_pattern, content)):
             content = "[CONTENT REDACTED DUE TO CONTACT INFO]"

    return content, has_violation

def scan_image_for_violations(image_file, user):
    if not image_file:
        return False
        
    try:
        from PIL import Image
        import pytesseract
        import re
        
        # Read the image
        image_file.seek(0)
        img = Image.open(image_file)
        text = pytesseract.image_to_string(img)
        
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b'
        
        if re.search(email_pattern, text, re.IGNORECASE) or re.search(phone_pattern, text):
            from ..models import Violation
            user.violation_count += 1
            duration_hours = get_ban_duration(user.violation_count)
            from django.utils import timezone
            from datetime import timedelta
            user.ban_until = timezone.now() + timedelta(hours=duration_hours)
            user.save()
            
            Violation.objects.create(
                user=user,
                description=f"Direct contact info shared in MEDIA. Banned for {duration_hours}h."
            )
            return True
    except Exception:
        # If pytesseract or PIL is not available, or other errors, skip for now
        # but in a production environment, this should be logged.
        pass
    finally:
        try:
            image_file.seek(0)
        except Exception:
            pass
            
    return False
