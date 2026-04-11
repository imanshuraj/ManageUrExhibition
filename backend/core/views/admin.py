from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
import csv
from functools import wraps
from ..models import User, VendorProfile, Project, Proposal, Message, Payment, Violation, JobPosting, JobApplication
from ..forms import SiteInspectorCreationForm, AdminCreationForm

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated: return redirect('login')
        
        # Globally enforce Owner role for the 'admin' username
        if request.user.username == 'admin' and request.user.role != User.Role.OWNER:
            request.user.role = User.Role.OWNER
            request.user.save()

        if not (request.user.is_superuser or request.user.is_staff or request.user.role in [User.Role.OWNER, User.Role.ADMIN]):
            messages.error(request, "Access denied. Administrative authority required."); return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped

def get_admin_context(role_filter=None):
    """Helper to consistently fetch admin dashboard data."""
    users_query = User.objects.all()
    if role_filter:
        users_query = users_query.filter(role=role_filter)
    
    return {
        'total_users': User.objects.count(),
        'total_exhibitors': User.objects.filter(role=User.Role.EXHIBITOR).count(),
        'total_vendors': User.objects.filter(role=User.Role.VENDOR).count(),
        'total_inspectors': User.objects.filter(role=User.Role.INSPECTOR).count(),
        'total_admins': User.objects.filter(role__in=[User.Role.OWNER, User.Role.ADMIN]).count(),
        'total_projects': Project.objects.count(),
        'open_projects': Project.objects.filter(status=Project.Status.OPEN).count(),
        'total_payments': Payment.objects.aggregate(t=Sum('amount'))['t'] or 0,
        'flagged_messages': Message.objects.filter(is_flagged=True).count(),
        'all_users': users_query.order_by('-date_joined'),
        'all_projects': Project.objects.select_related('exhibitor', 'assigned_vendor').order_by('-created_at'),
        'all_payments': Payment.objects.select_related('milestone__project').order_by('-created_at'),
        'flagged_msgs': Message.objects.filter(is_flagged=True).order_by('-created_at'),
        'vendor_profiles': VendorProfile.objects.select_related('user').all(),
        'all_inspectors': User.objects.filter(role=User.Role.INSPECTOR),
        'all_admins': User.objects.filter(role__in=[User.Role.OWNER, User.Role.ADMIN]),
        'all_violations': Violation.objects.select_related('user').order_by('-created_at'),
        'pending_count': VendorProfile.objects.filter(verification_status=VendorProfile.VerificationStatus.PENDING).count(),
        'project_statuses': Project.Status.choices,
        'user_roles': User.Role.choices,
        'current_role_filter': role_filter,
    }

@admin_required
def admin_dashboard(request):
    role_filter = request.GET.get('role')
    context = get_admin_context(role_filter)
    context['inspector_form'] = SiteInspectorCreationForm()
    context['admin_form'] = AdminCreationForm()
    return render(request, 'core/admin_dashboard.html', context)

@admin_required
def admin_bulk_delete_users(request):
    if request.method == 'POST':
        if request.user.role != User.Role.OWNER and not request.user.is_superuser:
            messages.error(request, "Only the System Owner can perform bulk deletions.")
            return redirect('admin_dashboard')
        user_ids = request.POST.getlist('user_ids')
        if user_ids:
            deleted_count, _ = User.objects.filter(id__in=user_ids).exclude(is_superuser=True).exclude(id=request.user.id).delete()
            messages.success(request, f"Successfully deleted {deleted_count} users.")
    return redirect('admin_dashboard')

@admin_required
def admin_delete_all_users(request):
    if request.method == 'POST':
        if request.user.role != User.Role.OWNER and not request.user.is_superuser:
            messages.error(request, "CRITICAL PROTECTION: Only the System Owner can clear the entire directory.")
            return redirect('admin_dashboard')
        deleted_count, _ = User.objects.exclude(is_superuser=True).exclude(id=request.user.id).delete()
        messages.success(request, f"Successfully deleted all {deleted_count} non-owner users.")
    return redirect('admin_dashboard')

@admin_required
def admin_bulk_export_users(request):
    user_ids = request.POST.getlist('user_ids')
    if not user_ids:
        return redirect('admin_dashboard')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="selected_users.csv"'
    w = csv.writer(response)
    w.writerow(['ID', 'Username', 'Email', 'Role', 'Joined'])
    
    for u in User.objects.filter(id__in=user_ids):
        w.writerow([u.id, u.username, u.email, u.get_role_display(), u.date_joined.strftime("%Y-%m-%d")])
    return response

@admin_required
def admin_verify_vendor(request, vendor_id):
    p = get_object_or_404(VendorProfile, pk=vendor_id)
    if p.verification_status == VendorProfile.VerificationStatus.VERIFIED:
        p.verification_status = VendorProfile.VerificationStatus.PENDING; p.user.is_verified = False
        messages.info(request, f"Vendor {p.user.username} verification revoked.")
    else:
        p.verification_status = VendorProfile.VerificationStatus.VERIFIED; p.user.is_verified = True
        messages.success(request, f"Vendor {p.user.username} verified successfully.")
    p.save(); p.user.save()
    return redirect('admin_dashboard')

@admin_required
def admin_reject_vendor(request, vendor_id):
    p = get_object_or_404(VendorProfile, pk=vendor_id)
    p.verification_status = VendorProfile.VerificationStatus.REJECTED; p.user.is_verified = False
    p.save(); p.user.save()
    messages.warning(request, f"Vendor {p.user.username} has been rejected.")
    return redirect('admin_dashboard')

@admin_required
def admin_delete_user(request, user_id):
    u = get_object_or_404(User, pk=user_id)
    if u.is_superuser or u.role == User.Role.OWNER:
        messages.error(request, "Primary Administrative Profiles cannot be deleted through this interface.")
    elif u == request.user:
        messages.error(request, "You cannot delete your own account.")
    else:
        u.delete()
        messages.success(request, f"User {u.username} has been permanently removed.")
    return redirect('admin_dashboard')

@admin_required
def admin_update_project_status(request, pk):
    p = get_object_or_404(Project, pk=pk)
    s = request.POST.get('status')
    if s in [c[0] for c in Project.Status.choices]:
        p.status = s; p.save()
        messages.success(request, f"Project status updated to {p.get_status_display()}.")
    return redirect('/admin-panel/#projects')

@admin_required
def admin_delete_project(request, pk):
    if request.method == 'POST':
        p = get_object_or_404(Project, pk=pk)
        p.delete()
        messages.success(request, "Project deleted successfully.")
    return redirect('/admin-panel/#projects')

@admin_required
def admin_toggle_flag_message(request, msg_id):
    m = get_object_or_404(Message, pk=msg_id); m.is_flagged = not m.is_flagged; m.save()
    status = "flagged" if m.is_flagged else "unflagged"
    messages.info(request, f"Message {status}.")
    return redirect('admin_dashboard')

@admin_required
def admin_delete_message(request, msg_id):
    get_object_or_404(Message, pk=msg_id).delete(); messages.success(request, "Message deleted.")
    return redirect('admin_dashboard')

@admin_required
def admin_delete_violation(request, violation_id):
    get_object_or_404(Violation, pk=violation_id).delete(); messages.success(request, "Violation record cleared.")
    return redirect('admin_dashboard')

@admin_required
def admin_toggle_staff(request, user_id):
    u = get_object_or_404(User, pk=user_id)
    if u != request.user:
        u.is_staff = not u.is_staff; u.save()
        status = "granted staff access" if u.is_staff else "revoked staff access"
        messages.success(request, f"Successfully {status} for {u.username}.")
    return redirect('admin_dashboard')

@admin_required
def admin_create_inspector(request):
    if request.method == 'POST':
        if request.user.role != User.Role.OWNER and not request.user.is_superuser:
            messages.error(request, "AUTHORITY ERROR: Only the System Owner can commission new Site Inspectors.")
            return redirect('admin_dashboard')
        form = SiteInspectorCreationForm(request.POST, request.FILES)
        if form.is_valid():
            u = form.save(commit=False)
            u.role = User.Role.INSPECTOR
            u.is_staff = False
            u.set_password(form.cleaned_data['password'])
            u.save()
            messages.success(request, f"Inspector {u.username} created and onboarded.")
            return redirect('admin_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    return redirect('admin_dashboard')

@admin_required
def admin_create_admin(request):
    if request.method == 'POST':
        if request.user.role != User.Role.OWNER and not request.user.is_superuser:
            messages.error(request, "AUTHORITY ERROR: Only the System Owner can authorize new Admin Staff profiles.")
            return redirect('admin_dashboard')
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            u = form.save(commit=False)
            u.role = User.Role.ADMIN  # Always created as Admin Staff
            u.is_staff = True
            u.set_password(form.cleaned_data['password'])
            u.save()
            messages.success(request, f"Admin Staff account for {u.username} has been established.")
            return redirect('admin_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    return redirect('admin_dashboard')

@admin_required
def admin_promote_to_admin(request, user_id):
    u = get_object_or_404(User, pk=user_id)
    u.role = User.Role.ADMIN; u.is_staff = True; u.save()
    messages.success(request, f"{u.username} has been promoted to Admin Staff.")
    return redirect('admin_dashboard')

@admin_required
def admin_manage_jobs(request):
    if request.method == 'POST':
        t, d, l = request.POST.get('title'), request.POST.get('description'), request.POST.get('location')
        if t and d and l:
            JobPosting.objects.create(title=t, description=d, location=l)
            messages.success(request, "Job posting created.")
    jobs = JobPosting.objects.all().order_by('-created_at')
    return render(request, 'core/admin_manage_jobs.html', {'jobs': jobs})

@admin_required
def admin_toggle_job(request, job_id):
    j = get_object_or_404(JobPosting, pk=job_id); j.is_active = not j.is_active; j.save()
    messages.info(request, "Job status toggled.")
    return redirect('admin_manage_jobs')

@admin_required
def admin_view_applications(request, job_id):
    j = get_object_or_404(JobPosting, pk=job_id); apps = j.applications.all()
    return render(request, 'core/admin_view_applications.html', {'job': j, 'applications': apps, 'status_choices': JobApplication.Status.choices})

@admin_required
def admin_delete_application(request, job_id, app_id):
    get_object_or_404(JobApplication, pk=app_id).delete()
    messages.success(request, "Application removed.")
    return redirect('admin_view_applications', job_id=job_id)

@admin_required
def admin_update_application_status(request, job_id, app_id):
    a = get_object_or_404(JobApplication, pk=app_id); s = request.POST.get('status')
    if s in dict(JobApplication.Status.choices):
        a.status = s; a.save()
        messages.success(request, "Application status updated.")
    return redirect('admin_view_applications', job_id=job_id)

@admin_required
def admin_export_users(request):
    response = HttpResponse(content_type='text/csv'); response['Content-Disposition'] = 'attachment; filename="users.csv"'
    w = csv.writer(response); w.writerow(['ID', 'Username', 'Email', 'Role'])
    for u in User.objects.all(): w.writerow([u.id, u.username, u.email, u.get_role_display()])
    return response

@admin_required
def admin_export_vendors(request):
    response = HttpResponse(content_type='text/csv'); response['Content-Disposition'] = 'attachment; filename="vendors.csv"'
    w = csv.writer(response); w.writerow(['ID', 'Username', 'Email', 'Rating'])
    for p in VendorProfile.objects.all(): w.writerow([p.user.id, p.user.username, p.user.email, p.rating])
    return response

@admin_required
def admin_export_projects(request):
    response = HttpResponse(content_type='text/csv'); response['Content-Disposition'] = 'attachment; filename="projects.csv"'
    w = csv.writer(response); w.writerow(['ID', 'Title', 'Exhibitor', 'Status'])
    for p in Project.objects.all(): w.writerow([p.id, p.title, p.exhibitor.username, p.get_status_display()])
    return response

@admin_required
def admin_export_payments(request):
    response = HttpResponse(content_type='text/csv'); response['Content-Disposition'] = 'attachment; filename="payments.csv"'
    w = csv.writer(response); w.writerow(['ID', 'Amount', 'Status'])
    for p in Payment.objects.all(): w.writerow([p.id, p.amount, p.get_status_display()])
    return response

@admin_required
def admin_export_messages(request):
    response = HttpResponse(content_type='text/csv'); response['Content-Disposition'] = 'attachment; filename="flagged_messages.csv"'
    w = csv.writer(response); w.writerow(['ID', 'Sender', 'Content'])
    for m in Message.objects.filter(is_flagged=True): w.writerow([m.id, m.sender.username, m.content])
    return response

@admin_required
def admin_export_violations(request):
    response = HttpResponse(content_type='text/csv'); response['Content-Disposition'] = 'attachment; filename="violations.csv"'
    w = csv.writer(response); w.writerow(['ID', 'User', 'Description'])
    for v in Violation.objects.all(): w.writerow([v.id, v.user.username, v.description])
    return response

@admin_required
def admin_export_jobs(request):
    response = HttpResponse(content_type='text/csv'); response['Content-Disposition'] = 'attachment; filename="careers.csv"'
    w = csv.writer(response); w.writerow(['ID', 'Title', 'Location'])
    for j in JobPosting.objects.all(): w.writerow([j.id, j.title, j.location])
    return response

@admin_required
def admin_export_applications(request, job_id):
    j = get_object_or_404(JobPosting, pk=job_id); response = HttpResponse(content_type='text/csv'); response['Content-Disposition'] = 'attachment; filename="applications.csv"'
    w = csv.writer(response); w.writerow(['ID', 'Candidate', 'Status'])
    for a in j.applications.all(): w.writerow([a.id, a.candidate_name, a.get_status_display()])
    return response
