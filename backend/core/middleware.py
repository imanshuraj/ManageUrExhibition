from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse

class BanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Safety check: if DB schema is out of sync, don't crash the whole site
            try:
                # If user is suspended or temporarily banned, log them out and redirect to home
                is_suspended = getattr(request.user, 'is_suspended', False)
                is_banned = request.user.ban_until and request.user.ban_until > timezone.now()

                if (is_suspended or is_banned) and not request.path.startswith('/admin/'):
                    from django.contrib.auth import logout
                    reason = "Account Suspended (3+ violations in a week)" if is_suspended else f"Temporary restriction until {request.user.ban_until.strftime('%d M, H:i')}"
                    
                    # Store message before logout
                    messages.error(request, f"Access Denied: {reason}. Please contact support if you believe this is an error.")
                    logout(request)
                    return redirect('home')
            except Exception:
                # If ban_until column is missing or fails, just proceed
                pass
        
        response = self.get_response(request)
        return response
