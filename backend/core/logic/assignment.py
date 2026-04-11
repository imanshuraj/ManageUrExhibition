from ..models import User, Project
from django.db.models import Count
def assign_site_inspector(project):
    inspectors = User.objects.filter(role=User.Role.INSPECTOR, is_active=True).order_by('id')
    if not inspectors.exists():
        return 
    if project.location:
        for inspector in inspectors:
            assignment_count = Project.objects.filter(
                location=project.location,
                assigned_site_inspector=inspector
            ).count()
            if assignment_count < 5:
                project.assigned_site_inspector = inspector
                project.save()
                return
    from django.db.models import Count
    least_busy = inspectors.annotate(
        num_assigned=Count('assigned_site_inspections')
    ).order_by('num_assigned').first()
    if least_busy:
        project.assigned_site_inspector = least_busy
        project.save()