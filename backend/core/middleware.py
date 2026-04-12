from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse

class BanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if user is currently banned
            if request.user.ban_until and request.user.ban_until > timezone.now():
                # Allow access to logout and maybe homepage/support
                allowed_paths = [reverse('logout'), '/support/', '/about/']
                if request.path not in allowed_paths and not request.path.startswith('/admin/'):
                    remaining_time = request.user.ban_until - timezone.now()
                    hours = int(remaining_time.total_seconds() // 3600)
                    minutes = int((remaining_time.total_seconds() % 3600) // 60)
                    
                    return render(request, 'core/restricted.html', {
                        'ban_until': request.user.ban_until,
                        'hours': hours,
                        'minutes': minutes,
                        'reason': "Shared contact information before payment completion."
                    })
        
        response = self.get_response(request)
        return response
