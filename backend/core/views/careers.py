from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import JobPosting, JobApplication
def careers_list(request):
    jobs = JobPosting.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'core/careers.html', {'jobs': jobs})

def apply_job(request, job_id):
    job = get_object_or_404(JobPosting, pk=job_id, is_active=True)
    if request.method == 'POST':
        name, email = request.POST.get('candidate_name'), request.POST.get('candidate_email')
        res = request.FILES.get('resume')
        if name and email and res:
            JobApplication.objects.create(job=job, candidate_name=name, candidate_email=email, resume=res)
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('careers_list')
    return render(request, 'core/apply_job.html', {'job': job})
