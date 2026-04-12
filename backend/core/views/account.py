from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib import messages
from ..forms import (CustomUserCreationForm, VendorProfileForm, ProfileUpdateForm)
from ..models import User, Project, Proposal, VendorProfile, Milestone, Venue
# Removed SAP Integration Connector
DEFAULT_OTP = '123456'

def home(request):
    try:
        # Force execution with list() to catch missing table/column errors early
        live_projects = list(Project.objects.filter(
            status=Project.Status.OPEN
        ).order_by('-created_at')[:6])
    except Exception:
        live_projects = []
        
    try:
        # Force execution with list()
        venues = list(Venue.objects.all())
    except Exception:
        venues = []
        
    return render(request, 'core/home.html', {
        'live_projects': live_projects,
        'venues': venues
    })

def custom_login(request):
    if request.user.is_authenticated:
        if (request.user.is_staff or request.user.is_superuser or request.user.role in [User.Role.ADMIN, User.Role.OWNER]) and request.user.role != User.Role.INSPECTOR:
            return redirect('admin_dashboard')
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if (user.is_staff or user.is_superuser or user.role in [User.Role.ADMIN, User.Role.OWNER]) and user.role != User.Role.INSPECTOR:
                return redirect('admin_dashboard')
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control rounded-3'
        
    return render(request, 'core/login.html', {'form': form})

def signup_choice(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/signup_choice.html')

def exhibitor_signup(request):
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['role'] = User.Role.EXHIBITOR
        form = CustomUserCreationForm(post_data)
        otp_entered = request.POST.get('otp', '').strip()
        otp_valid = (otp_entered == DEFAULT_OTP)
        if form.is_valid() and otp_valid:
            user = form.save(commit=False)
            user.role = User.Role.EXHIBITOR
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session['registration_success'] = True
            request.session['registration_role'] = 'Exhibitor'
            return redirect('dashboard')
        elif not otp_valid:
            messages.error(request, 'Invalid OTP. Please enter the correct OTP.')
    else:
        form = CustomUserCreationForm(initial={'role': User.Role.EXHIBITOR})
        form.fields['role'].widget.attrs['disabled'] = True
    return render(request, 'core/signup.html', {'form': form, 'title': 'Exhibitor Sign Up'})

def vendor_signup(request):
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['role'] = User.Role.VENDOR
        user_form = CustomUserCreationForm(post_data)
        profile_form = VendorProfileForm(request.POST)
        otp_entered = request.POST.get('otp', '').strip()
        otp_valid = (otp_entered == DEFAULT_OTP)
        if user_form.is_valid() and profile_form.is_valid() and otp_valid:
            user = user_form.save(commit=False)
            user.role = User.Role.VENDOR
            if not all([user.bank_account_number, user.ifsc_code, user.bank_name]):
                messages.error(request, "Bank account details (Number, IFSC, and Bank Name) are mandatory for Vendors.")
                return render(request, 'core/vendor_signup.html', {'user_form': user_form, 'profile_form': profile_form})
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            profile_form.save_m2m()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session['registration_success'] = True
            request.session['registration_role'] = 'Vendor'
            return redirect('dashboard')
        elif not otp_valid:
            messages.error(request, 'Invalid OTP. Please enter the correct OTP.')
    else:
        user_form = CustomUserCreationForm(initial={'role': User.Role.VENDOR})
        user_form.fields['role'].widget.attrs['disabled'] = True
        profile_form = VendorProfileForm()
    return render(request, 'core/vendor_signup.html', {'user_form': user_form, 'profile_form': profile_form})

@login_required
def dashboard(request):
    show_registration_success = request.session.pop('registration_success', False)
    registration_role = request.session.pop('registration_role', '')
    if (request.user.is_staff or request.user.is_superuser or request.user.role == User.Role.ADMIN) and request.user.role != User.Role.INSPECTOR:
        return redirect('admin_dashboard')
    is_subscribed = request.user.has_active_subscription
    if request.user.role == User.Role.EXHIBITOR:
        projects = Project.objects.filter(exhibitor=request.user)
        active_count = projects.filter(status=Project.Status.OPEN).count()
        completed_count = projects.filter(status=Project.Status.COMPLETED).count()
        recent_projects = projects.order_by('-created_at')[:3]
        context = {
            'active_count': active_count,
            'completed_count': completed_count,
            'recent_projects': recent_projects,
            'show_registration_success': show_registration_success,
            'registration_role': registration_role,
            'is_subscribed': is_subscribed,
        }
        return render(request, 'core/exhibitor_dashboard.html', context)
    elif request.user.role == User.Role.VENDOR:
        try:
            proposals = Proposal.objects.filter(vendor=request.user)
            active_bids_count = proposals.filter(status=Proposal.Status.PENDING).count()
            assigned_projects = Project.objects.filter(assigned_vendor=request.user).order_by('-updated_at')
            projects_won_count = assigned_projects.count()
            
            try:
                vendor_categories = request.user.vendor_profile.categories.all()
            except Exception:
                vendor_categories = []
            
            from django.db.models import Q
            recommended_projects = Project.objects.filter(
                Q(status=Project.Status.OPEN) |
                Q(proposals__vendor=request.user)
            ).distinct().order_by('-created_at')[:3]
        except Exception:
            proposals = []
            active_bids_count = 0
            assigned_projects = []
            projects_won_count = 0
            vendor_categories = []
            recommended_projects = []
        
        context = {
            'active_bids_count': active_bids_count,
            'projects_won_count': projects_won_count,
            'assigned_projects': assigned_projects[:5] if hasattr(assigned_projects, '__getitem__') else assigned_projects,
            'recommended_projects': recommended_projects,
            'show_registration_success': show_registration_success,
            'registration_role': registration_role,
            'is_subscribed': is_subscribed,
        }
        return render(request, 'core/vendor_dashboard.html', context)
    elif request.user.role == User.Role.INSPECTOR:
        try:
            assigned_projects = Project.objects.filter(assigned_site_inspector=request.user).order_by('-created_at')
            pending_inspections = Milestone.objects.filter(project__assigned_site_inspector=request.user, status=Milestone.Status.COMPLETED).count()
            failure_reports = Project.objects.filter(assigned_site_inspector=request.user, is_under_failure_review=True)
        except Exception:
            assigned_projects = []
            pending_inspections = 0
            failure_reports = []
        context = {
            'assigned_projects': assigned_projects,
            'pending_inspections': pending_inspections,
            'failure_reports': failure_reports,
            'show_registration_success': show_registration_success,
            'registration_role': 'Site Inspector',
            'is_subscribed': True, 
        }
        return render(request, 'core/inspector_dashboard.html', context)
    return redirect('home')

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('dashboard')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'core/edit_profile.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'core/change_password.html', {'form': form})
