from ..models import User, Project
from django.db.models import Count, Q

def assign_site_inspector(project):
    """
    Assigns a Site Inspector to a project based on:
    1. Maximum 5 projects per inspector on the same date.
    2. All projects on the same date must be at the same venue.
    """
    inspectors = User.objects.filter(role=User.Role.INSPECTOR, is_active=True)
    
    if not inspectors.exists():
        return

    target_date = project.event_date
    target_venue = project.venue

    if not target_date or not target_venue:
        # Fallback: Assign to the least busy inspector globally if date/venue is missing
        least_busy = inspectors.annotate(
            num_assigned=Count('assigned_site_inspections')
        ).order_by('num_assigned').first()
        
        if least_busy:
            project.assigned_site_inspector = least_busy
            project.save()
        return

    # Find a suitable inspector
    suitable_inspectors = []

    for inspector in inspectors:
        # Get all active assignments for this inspector on the target date
        assignments_on_date = Project.objects.filter(
            assigned_site_inspector=inspector,
            event_date=target_date,
            status__in=[Project.Status.ASSIGNED, Project.Status.IN_PROGRESS]
        )
        
        count_on_date = assignments_on_date.count()
        
        if count_on_date >= 5:
            continue # Reached max capacity for this date
            
        if count_on_date > 0:
            # Check if all assignments on this date are at the same venue
            # Since we enforce this rule, checking the first one is sufficient
            # But let's check all just in case
            if assignments_on_date.exclude(venue=target_venue).exists():
                continue # Has assignments at a different venue on the same date

        suitable_inspectors.append(inspector)

    if suitable_inspectors:
        # Sort suitable inspectors to prefer those who already have assignments at this venue on this date
        # to clump works together, or alternatively, just pick the one with fewest total assignments
        def get_inspector_score(insp):
            # Prefer inspectors who already are at the venue on this date
            has_venue_assignment = Project.objects.filter(
                assigned_site_inspector=insp,
                event_date=target_date,
                venue=target_venue,
                status__in=[Project.Status.ASSIGNED, Project.Status.IN_PROGRESS]
            ).exists()
            total_assigned = Project.objects.filter(assigned_site_inspector=insp).count()
            return (not has_venue_assignment, total_assigned)
            
        best_inspector = sorted(suitable_inspectors, key=get_inspector_score)[0]
        project.assigned_site_inspector = best_inspector
        project.save()
        return

    # If no suitable inspector found (e.g., everyone is full or at different venues)
    # We might leave it unassigned or fallback. Let's leave unassigned for admin to handle manually
    # or fallback to least busy? The prompt implies strict rules.
    # "if locaion varries than it is allocated to diffrent site inspector"
    # What if ALL inspectors are maxed out or at different venues?
    # We will leave it unassigned (or we could fallback to any inspector, but strict constraint implies no).
    pass