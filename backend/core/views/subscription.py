from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import datetime
from ..models import Subscription

@login_required
def subscription_plans(request):
    exhibitor_plans = [
        {'id': 'e_1', 'name': 'Startup Bundle', 'price': 5000, 'posts_allowed': 1},
        {'id': 'e_2', 'name': 'Growth Bundle', 'price': 8000, 'posts_allowed': 2},
        {'id': 'e_3', 'name': 'Business Bundle', 'price': 12000, 'posts_allowed': 4},
        {'id': 'e_4', 'name': 'Enterprise Bundle', 'price': 15000, 'posts_allowed': 7},
        {'id': 'e_5', 'name': 'Kingdom Bundle', 'price': 18000, 'posts_allowed': 10},
    ]
    vendor_plans = [
        {'id': 'v_daily', 'name': 'Daily Pass', 'price': 1000},
        {'id': 'v_monthly', 'name': 'Enterprise Monthly', 'price': 15000},
    ]
    return render(request, 'core/subscription_plans.html', {
        'exhibitor_plans': exhibitor_plans,
        'vendor_plans': vendor_plans
    })

@login_required
def subscribe_process(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        plans = {
            'v_daily':   {'name': 'Vendor Daily',   'price': 1000,   'days': 1,    'posts': 0},
            'v_weekly':  {'name': 'Vendor Weekly',  'price': 5000,   'days': 7,    'posts': 0},
            'v_monthly': {'name': 'Vendor Monthly', 'price': 15000,  'days': 30,   'posts': 0},
            'v_yearly':  {'name': 'Vendor Yearly',  'price': 100000, 'days': 365,  'posts': 0},
            'e_1': {'name': 'Exhibitor - 1 Post',  'price': 5000,  'days': 365, 'posts': 1},
            'e_2': {'name': 'Exhibitor - 2 Posts', 'price': 8000,  'days': 365, 'posts': 2},
            'e_3': {'name': 'Exhibitor - 4 Posts', 'price': 12000, 'days': 365, 'posts': 4},
            'e_4': {'name': 'Exhibitor - 7 Posts', 'price': 15000, 'days': 365, 'posts': 7},
            'e_5': {'name': 'Exhibitor - 10 Posts', 'price': 18000, 'days': 365, 'posts': 10},
        }
        plan = plans.get(plan_id)
        if not plan:
            messages.error(request, "Invalid plan selected.")
            return redirect('subscription_plans')
        request.user.subscriptions.filter(is_active=True).update(is_active=False)
        Subscription.objects.create(
            user=request.user,
            plan_name=plan['name'],
            amount=plan['price'],
            end_date=timezone.now() + datetime.timedelta(days=plan['days']),
            posts_allowed=plan['posts']
        )
        messages.success(request, f"Plan '{plan['name']}' activated successfully!")
        return redirect('dashboard')
    return redirect('subscription_plans')
