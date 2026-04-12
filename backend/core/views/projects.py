from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from functools import wraps
from ..models import User, Project, Proposal, Message, Subscription, ProjectMedia, ProposalMedia
from ..forms import (ProjectForm, ProposalForm, MessageForm, MilestoneForm)
from ..logic.assignment import assign_site_inspector

def subscription_required(view_func):
    """Only used for CREATE PROJECT – requires an active subscription/post bundle."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == User.Role.ADMIN):
            if not request.user.has_active_subscription:
                if request.user.role == User.Role.EXHIBITOR:
                    messages.warning(request, "You need an active project posting bundle to post a new project.")
                else:
                    messages.warning(request, "An active subscription is required.")
                return redirect('subscription_plans')
        return view_func(request, *args, **kwargs)
    return _wrapped


def vendor_subscription_required_for_new_bid(view_func):
    """Vendors need a subscription only to submit a FIRST proposal on a project.
    If they already have a proposal on this project (resend case) allow through freely."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role == User.Role.VENDOR:
            if not request.user.has_active_subscription:
                already_engaged = False
                # submit_proposal passes pk (project pk)
                project_pk = kwargs.get('pk')
                if project_pk:
                    already_engaged = Proposal.objects.filter(
                        vendor=request.user,
                        project__pk=project_pk
                    ).exists()
                # resend_proposal passes proposal_id – look up via the proposal
                proposal_id = kwargs.get('proposal_id')
                if proposal_id:
                    already_engaged = Proposal.objects.filter(
                        vendor=request.user,
                        pk=proposal_id
                    ).exists()
                if not already_engaged:
                    messages.warning(request, "An active subscription is required to submit new proposals.")
                    return redirect('subscription_plans')
        return view_func(request, *args, **kwargs)
    return _wrapped

@login_required
def create_project(request):
    if request.user.role != User.Role.EXHIBITOR:
        messages.error(request, "Only Exhibitors can create projects.")
        return redirect('dashboard')
    
    # Auto-Seed Categories
    from ..models import Category
    default_cats = [
        "Stall Design & Fabrication (Wooden)",
        "Octanorm / Maxima Stall System",
        "Printing & Branding (Vinyl, Fabric)",
        "Audio Visual & LED Walls",
        "Furniture & Props Rental",
        "Host / Hostess & Manpower",
        "Photography & Videography",
        "Event Marketing & PR",
        "Catering & Hospitality Services",
        "Translation & Interpretation",
        "Security & Crowd Control",
        "Cleaning & Waste Management",
        "Logistics & Freight Forwarding",
        "Virtual & Hybrid Event Tech",
        "Floral & Decor Arrangements",
        "General Contracting & Labor",
        "Overall Package"
    ]
    for cat_name in default_cats:
        Category.objects.get_or_create(name=cat_name)
    
    # Auto-Seed Venues
    from ..models import Venue
    default_venues = [
        "Pragati Maidan, New Delhi",
        "BEC Nesco, Mumbai",
        "BIEC, Bangalore",
        "HITEX, Hyderabad",
        "Jio World Centre, Mumbai",
        "India Expo Mart, Greater Noida",
        "Chennai Trade Centre, Chennai",
        "Biswa Bangla Mela Prangan, Kolkata",
        "Other"
    ]
    for v_name in default_venues:
        Venue.objects.get_or_create(name=v_name)

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            from ..utils import filter_chat_message
            project = form.save(commit=False)
            project.exhibitor = request.user
            
            # Check for contact info violation in description
            filtered_desc, flagged = filter_chat_message(project.description, request.user)
            if flagged:
                project.description = filtered_desc
                messages.warning(request, "Contact information detected and redacted. Your account has been temporarily restricted.")
            
            # Check for violation in title/venue_details? (Optional but good)
            filtered_title, _ = filter_chat_message(project.title, request.user)
            project.title = filtered_title
            
            project.save()
            
            if flagged:
                return redirect('dashboard')
            # Save multiple media files
            files = request.FILES.getlist('additional_media_files')
            for f in files[:10]:
                ProjectMedia.objects.create(project=project, file=f)
            messages.success(request, "Project created successfully!")
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'core/create_project.html', {'form': form})

@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user.role != User.Role.EXHIBITOR or project.exhibitor != request.user:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    if project.status != Project.Status.OPEN:
        messages.error(request, "Assigned projects cannot be modified. Please contact support or the site inspector for changes.")
        return redirect('project_detail', pk=pk)

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            project = form.save()
            # Save multiple media files if provided
            files = request.FILES.getlist('additional_media_files')
            for f in files[:10]:
                ProjectMedia.objects.create(project=project, file=f)
            messages.success(request, "Project updated successfully!")
            return redirect('project_detail', pk=pk)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'core/create_project.html', {
        'form': form, 
        'project': project, 
        'is_edit': True
    })

@login_required
def project_list(request):
    if request.user.role == User.Role.EXHIBITOR:
        projects = Project.objects.filter(exhibitor=request.user).order_by('-created_at')
        template = 'core/exhibitor_project_list.html'
    elif request.user.role == User.Role.VENDOR:
        from django.db.models import Q
        vendor_categories = request.user.vendor_profile.categories.all()
        projects = Project.objects.filter(
            Q(status=Project.Status.OPEN) |
            Q(proposals__vendor=request.user)
        ).distinct().order_by('-created_at')
        template = 'core/vendor_project_list.html'
    else:
        return redirect('dashboard')
    return render(request, template, {'projects': projects, 'is_subscribed': request.user.has_active_subscription})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user.role == User.Role.EXHIBITOR and project.exhibitor != request.user:
        return redirect('dashboard')
    
    # Access control for Vendors on non-OPEN projects
    if request.user.role == User.Role.VENDOR and project.status != Project.Status.OPEN:
        has_bid = project.proposals.filter(vendor=request.user).exists()
        if not has_bid:
            messages.error(request, "This project is no longer accepting new proposals.")
            return redirect('dashboard')

    proposals = list(project.proposals.exclude(status=Proposal.Status.RESENT).order_by('-created_at'))
    if request.user.role == User.Role.EXHIBITOR:
        from ..utils import calculate_vendor_score
        for p in proposals:
            if hasattr(p.vendor, 'vendor_profile'):
                p.ai_score = calculate_vendor_score(p.vendor.vendor_profile, project)
            else:
                p.ai_score = 0
        proposals = sorted(proposals, key=lambda x: getattr(x, 'ai_score', 0), reverse=True)
        
    has_existing_proposal = False
    if request.user.role == User.Role.VENDOR:
        has_existing_proposal = any(p.vendor == request.user for p in proposals)

    accepted_proposal = project.proposals.filter(status=Proposal.Status.ACCEPTED).first()

    context = {
        'project': project,
        'proposals': proposals,
        'is_subscribed': request.user.has_active_subscription,
        'has_existing_proposal': has_existing_proposal,
        'accepted_proposal': accepted_proposal,
    }
    return render(request, 'core/project_detail.html', context)

@login_required
def submit_proposal(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user.role != User.Role.VENDOR:
        messages.error(request, "Only vendors can submit proposals.")
        return redirect('project_detail', pk=pk)
    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            from ..utils import filter_chat_message
            proposal = form.save(commit=False)
            proposal.project = project
            proposal.vendor = request.user
            
            # Check for violation (only if not paid)
            if not project.is_paid:
                filtered_desc, flagged = filter_chat_message(proposal.description, request.user, project)
                if flagged:
                    proposal.description = filtered_desc
                    messages.warning(request, "Contact information detected in proposal. Your account has been temporarily restricted.")
            
            proposal.save()
            
            if not project.is_paid and 'flagged' in locals() and flagged:
                return redirect('dashboard')
            # Save multiple media files
            files = request.FILES.getlist('additional_media_files')
            for f in files[:10]:
                ProposalMedia.objects.create(proposal=proposal, file=f)
            messages.success(request, "Proposal submitted successfully.")
            return redirect('project_detail', pk=pk)
    else:
        form = ProposalForm()
    return render(request, 'core/submit_proposal.html', {'form': form, 'project': project})

@login_required
def resend_proposal(request, proposal_id):
    original = get_object_or_404(Proposal, pk=proposal_id)
    if request.user.role != User.Role.VENDOR or original.vendor != request.user:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    if original.revision_count >= 5:
        messages.error(request, "You have reached the maximum of 5 revision allowed for a quotation.")
        return redirect('project_detail', pk=original.project.pk)
        
    project = original.project
    if request.method == 'POST':
        form = ProposalForm(request.POST, instance=original)
        if form.is_valid():
            from ..utils import timezone
            from ..utils import filter_chat_message
            updated_proposal = form.save(commit=False)
            updated_proposal.status = Proposal.Status.PENDING
            updated_proposal.is_resent = True
            updated_proposal.resent_at = timezone.now()
            updated_proposal.revision_count += 1
            
            # Check for violation
            if not project.is_paid:
                filtered_desc, flagged = filter_chat_message(updated_proposal.description, request.user, project)
                if flagged:
                    updated_proposal.description = filtered_desc
                    messages.warning(request, "Contact information detected in revised proposal. Your account has been temporarily restricted.")
            
            updated_proposal.save()
            
            if not project.is_paid and 'flagged' in locals() and flagged:
                return redirect('dashboard')
            # Handle updated media (clear old/add new? For now just add new)
            files = request.FILES.getlist('additional_media_files')
            for f in files[:10]:
                ProposalMedia.objects.create(proposal=updated_proposal, file=f)
            messages.success(request, "Revised quotation updated successfully!")
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProposalForm(initial={'amount': original.amount, 'description': original.description})
    return render(request, 'core/resend_proposal.html', {'form': form, 'project': project, 'original': original})

@login_required
def accept_proposal(request, proposal_id):
    proposal = get_object_or_404(Proposal, pk=proposal_id)
    project = proposal.project
    if request.user.role != User.Role.EXHIBITOR or project.exhibitor != request.user:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    if request.method == 'POST':
        if project.assigned_vendor:
            messages.error(request, "This project already has an assigned vendor.")
            return redirect('project_detail', pk=project.pk)
        
        proposal.status = Proposal.Status.ACCEPTED
        proposal.save()
        
        # Reject all other pending/resent proposals
        project.proposals.exclude(pk=proposal.pk).filter(status__in=[Proposal.Status.PENDING, Proposal.Status.RESENT]).update(status=Proposal.Status.REJECTED)
        
        project.assigned_vendor = proposal.vendor
        project.status = Project.Status.ASSIGNED
        project.save()
        
        messages.success(request, f"🎉 Quotation accepted! {proposal.vendor.company_name or proposal.vendor.username} has been assigned to your project. A site inspector will be allotted shortly.")
        return redirect('project_detail', pk=project.pk)
    return redirect('project_detail', pk=project.pk)

@login_required
def pay_for_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user != project.exhibitor:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    if request.method == 'POST':
        project.is_paid = True
        project.status = Project.Status.IN_PROGRESS
        project.save()
        assign_site_inspector(project)
        messages.success(request, "Payment successful! Admin holds funds in Escrow. Your project is now in progress.")
        return redirect('project_detail', pk=project.pk)
    return redirect('project_detail', pk=project.pk)

@login_required
def decline_proposal(request, proposal_id):
    proposal = get_object_or_404(Proposal, pk=proposal_id)
    project = proposal.project
    if request.user.role != User.Role.EXHIBITOR or project.exhibitor != request.user:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    if request.method == 'POST':
        proposal.status = Proposal.Status.REJECTED
        proposal.save()
        messages.warning(request, f"Proposal from '{proposal.vendor.username}' declined.")
        return redirect('project_detail', pk=project.pk)
    return redirect('project_detail', pk=project.pk)

@login_required
def project_chat(request, pk, vendor_id):
    project = get_object_or_404(Project, pk=pk)
    vendor = get_object_or_404(User, pk=vendor_id, role=User.Role.VENDOR)
    inspector = project.assigned_site_inspector

    # Access control: exhibitor, assigned vendor, or assigned inspector only
    allowed = False
    if request.user == project.exhibitor:
        allowed = True
    elif request.user == vendor and project.assigned_vendor == vendor:
        allowed = True
    elif inspector and request.user == inspector:
        allowed = True
    # Admins can also view
    elif request.user.is_staff or request.user.is_superuser or request.user.role == User.Role.ADMIN:
        allowed = True

    if not allowed:
        messages.error(request, "You don't have access to this chat.")
        return redirect('dashboard')

    # Enforce payment-first chat restriction (not for inspector)
    if not project.is_paid and request.user != inspector:
        messages.error(request, "Chat will be enabled once the escrow payment is completed by the exhibitor.")
        return redirect('project_detail', pk=project.pk)

    # Always use group messages — all 3 parties share one thread
    chat_messages = Message.objects.filter(
        project=project, is_group_message=True
    ).order_by('created_at').select_related('sender')

    # Mark as read for current user
    from ..models import MessageReadStatus
    unread = chat_messages.exclude(sender=request.user).exclude(read_statuses__user=request.user)
    for msg in unread:
        MessageReadStatus.objects.get_or_create(message=msg, user=request.user)

    # Re-fetch with prefetch for template efficiency
    chat_messages = chat_messages.prefetch_related('read_statuses__user')

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.cleaned_data.get('content', '')
            image = form.cleaned_data.get('image')
            from ..utils import filter_chat_message, scan_image_for_violations
            is_flagged = False
            filtered_content = content
            if content:
                filtered_content, text_flagged = filter_chat_message(content, request.user)
                if text_flagged:
                    is_flagged = True
            if image:
                if scan_image_for_violations(image, request.user):
                    is_flagged = True
                    messages.warning(request, "Image was flagged.")
            Message.objects.create(
                sender=request.user,
                receiver=None,
                project=project,
                content=filtered_content,
                image=image,
                file=form.cleaned_data.get('file'),
                is_flagged=is_flagged,
                is_group_message=True
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({'status': 'ok'})
            return redirect('project_chat', pk=pk, vendor_id=vendor_id)
        elif 'call_type' in request.POST:
            call_type = request.POST.get('call_type')
            if call_type in ['AUDIO', 'VIDEO']:
                Message.objects.create(
                    sender=request.user,
                    receiver=None,
                    project=project,
                    content=f"Invited to {call_type.lower()} call.",
                    is_call_link=True,
                    call_type=call_type,
                    is_group_message=True
                )
                return redirect('project_chat', pk=pk, vendor_id=vendor_id)
    else:
        form = MessageForm()

    accepted_proposal = project.proposals.filter(vendor=vendor, status=Proposal.Status.ACCEPTED).first()

    context = {
        'project': project,
        'vendor': vendor,
        'inspector': inspector,
        'chat_messages': chat_messages,
        'form': form,
        'accepted_proposal': accepted_proposal,
    }
    return render(request, 'core/project_chat.html', context)

@login_required
def project_milestones(request, pk):
    project = get_object_or_404(Project, pk=pk)
    milestones = project.milestones.all().order_by('due_date')
    return render(request, 'core/milestones.html', {'project': project, 'milestones': milestones})

@login_required
def create_milestone(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user.role != User.Role.EXHIBITOR:
        messages.error(request, "Only exhibitors can create milestones.")
        return redirect('project_milestones', pk=pk)
    if request.method == 'POST':
        form = MilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False); milestone.project = project; milestone.save()
            from ..models import Payment
            Payment.objects.create(milestone=milestone, amount=milestone.amount, status=Payment.Status.HELD)
            messages.success(request, f"Milestone '{milestone.title}' created.")
            return redirect('project_milestones', pk=pk)
    else:
        form = MilestoneForm()
    return render(request, 'core/create_milestone.html', {'form': form, 'project': project})

@login_required
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user != project.exhibitor:
        messages.error(request, "Access denied."); return redirect('dashboard')
    if project.status != Project.Status.OPEN:
        messages.error(request, "Assigned projects cannot be deleted. Use failure reporting if project is active.")
        return redirect('project_detail', pk=project.id)
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Project requirement deleted successfully.")
        return redirect('dashboard')
    return redirect('project_detail', pk=project.id)

@login_required
def report_vendor_failure(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.user != project.exhibitor:
        messages.error(request, "Access denied."); return redirect('dashboard')
    if project.status == Project.Status.OPEN:
        messages.error(request, "You can delete an open project directly."); return redirect('project_detail', pk=project.id)
    if not project.assigned_vendor:
        messages.error(request, "No vendor assigned."); return redirect('dashboard')
    if request.method == 'POST':
        project.is_under_failure_review = True; project.save()
        messages.success(request, "Failure report submitted. Site Inspector will verify.")
        return redirect('project_detail', pk=project.id)
    return redirect('project_detail', pk=project.id)
