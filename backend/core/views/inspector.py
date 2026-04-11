from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from ..models import User, Project, Milestone, Payment, Inspection
from ..forms import InspectionForm

@login_required
def inspector_dashboard(request):
    if request.user.role != User.Role.INSPECTOR:
        return redirect('dashboard')
    show_registration_success = request.session.pop('registration_success', False)
    assigned_projects = Project.objects.filter(assigned_site_inspector=request.user).order_by('-created_at')
    pending_inspections = Milestone.objects.filter(project__assigned_site_inspector=request.user, status=Milestone.Status.COMPLETED).count()
    failure_reports = Project.objects.filter(assigned_site_inspector=request.user, is_under_failure_review=True)
    context = {
        'assigned_projects': assigned_projects,
        'pending_inspections': pending_inspections,
        'failure_reports': failure_reports,
        'show_registration_success': show_registration_success,
        'registration_role': 'Site Inspector',
        'is_subscribed': True,
    }
    return render(request, 'core/inspector_dashboard.html', context)

@login_required
def inspect_milestone(request, milestone_id):
    milestone = get_object_or_404(Milestone, pk=milestone_id)
    if request.user.role != User.Role.INSPECTOR: return redirect('inspector_dashboard')
    if request.method == 'POST':
        form = InspectionForm(request.POST)
        if form.is_valid():
            insp = form.save(commit=False); insp.inspector = request.user; insp.project = milestone.project; insp.milestone = milestone; insp.save()
            if insp.status == Inspection.Status.PASS:
                milestone.status = Milestone.Status.VERIFIED; milestone.save()
                messages.success(request, "Milestone verified.")
            return redirect('project_milestones', pk=milestone.project.pk)
    else: form = InspectionForm()
    return render(request, 'core/inspect_milestone.html', {'form': form, 'milestone': milestone})

@login_required
def approve_inspection(request, inspection_id):
    insp = get_object_or_404(Inspection, pk=inspection_id)
    if request.user.role != User.Role.INSPECTOR: return redirect('inspector_dashboard')
    if request.method == 'POST':
        insp.is_approved_by_exhibitor = True; insp.save()
        ms = insp.milestone
        if ms and hasattr(ms, 'payment'):
            ms.status = Milestone.Status.APPROVED; ms.save()
            pay = ms.payment; pay.status = Payment.Status.RELEASED
            from django.utils import timezone
            pay.released_at = timezone.now(); pay.save()
            messages.success(request, f"Work approved! Payment of ₹{pay.amount} released.")
        return redirect('project_milestones', pk=insp.project.pk)
    return redirect('project_milestones', pk=insp.project.pk)

@login_required
def approve_failure_report(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.user != project.assigned_site_inspector:
        messages.error(request, "Access denied."); return redirect('inspector_dashboard')
    if request.method == 'POST':
        vendor = project.assigned_vendor
        reason = request.POST.get('failure_reason', 'Verified by Inspector.')
        if hasattr(vendor, 'vendor_profile'):
            vp = vendor.vendor_profile; vp.rating = max(0.0, vp.rating - 1.0); vp.save()
        sub = project.exhibitor.subscriptions.filter(is_active=True).first()
        if sub and sub.posts_used > 0: sub.posts_used -= 1; sub.save()
        project.assigned_vendor = None; project.status = Project.Status.OPEN
        project.is_under_failure_review = False; project.failure_reason = reason; project.save()
        messages.success(request, f"Vendor failure verified. Reason: {reason}")
        return redirect('inspector_dashboard')
    return redirect('project_detail', pk=project.id)

@login_required
def release_payment(request, milestone_id):
    ms = get_object_or_404(Milestone, pk=milestone_id)
    messages.info(request, "Use 'Approve Work' on the inspection report.")
    return redirect('project_milestones', pk=ms.project.pk)

@login_required
def inspector_rate_vendor(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.user.role != User.Role.INSPECTOR: return redirect('inspector_dashboard')
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 0))
        review = request.POST.get('review', '')
        Inspection.objects.create(inspector=request.user, project=project, report=review, status=Inspection.Status.PASS, vendor_rating=rating)
        if hasattr(project.assigned_vendor, 'vendor_profile'):
            vp = project.assigned_vendor.vendor_profile
            all_r = Inspection.objects.filter(project__assigned_vendor=project.assigned_vendor, vendor_rating__gt=0)
            avg = all_r.aggregate(a=Sum('vendor_rating'))['a']
            cnt = all_r.count()
            if cnt > 0: vp.rating = round(avg/cnt, 1); vp.save()
        messages.success(request, f"Rated {rating}/5 stars.")
    return redirect('inspector_dashboard')
