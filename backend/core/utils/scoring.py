def calculate_vendor_score(vendor_profile, project):
    score = 0
    if project.category in vendor_profile.categories.all():
        score += 40
    score += (vendor_profile.rating / 5.0) * 30
    completed = min(vendor_profile.total_projects_completed, 10)
    score += (completed / 10.0) * 20
    if vendor_profile.verification_status == 'VERIFIED':
        score += 10
    return min(round(score, 1), 100)
