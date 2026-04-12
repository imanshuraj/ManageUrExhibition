from ..models import User, Project, Venue
from django.db.models import Count

def assign_site_inspector(project):
    """
    Assigns a Site Inspector to a project based on:
    1. Venue match (if project has a venue)
    2. Workload limit (max 5 active projects in that venue)
    3. Fallback to least busy inspector if 'Other' or no venue match
    """
    inspectors = User.objects.filter(role=User.Role.INSPECTOR, is_active=True)
    
    if not inspectors.exists():
        return

    # 1. Try matching by Venue
    if project.venue:
        venue_inspectors = inspectors.filter(preferred_venue=project.venue)
        for inspector in venue_inspectors:
            assignment_count = Project.objects.filter(
                venue=project.venue,
                assigned_site_inspector=inspector,
                status__in=[Project.Status.ASSIGNED, Project.Status.IN_PROGRESS]
            ).count()
            
            if assignment_count < 5:
                project.assigned_site_inspector = inspector
                project.save()
                return
                
    # 2. Fallback: Assign to the least busy inspector globally
    least_busy = inspectors.annotate(
        num_assigned=Count('assigned_site_inspections')
    ).order_by('num_assigned').first()
    
    if least_busy:
        project.assigned_site_inspector = least_busy
        project.save()