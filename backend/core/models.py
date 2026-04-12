from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        ADMIN = 'ADMIN', 'Admin Staff'
        EXHIBITOR = 'EXHIBITOR', 'Exhibitor'
        VENDOR = 'VENDOR', 'Vendor'
        INSPECTOR = 'INSPECTOR', 'Site Inspector'
    
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EXHIBITOR)
    
    # Validation & Uniqueness
    phone_number = models.CharField(
        max_length=17,
        unique=True,
        null=True,
        blank=True,
        validators=[RegexValidator(r'^\+?[1-9]\d{6,14}$', 'Enter a valid phone number with country code.')],
        help_text="Stored as: +919876543210"
    )
    company_name = models.CharField(max_length=255, blank=True, null=True, unique=True)
    gst_number = models.CharField(
        max_length=15, 
        unique=True, 
        null=True, 
        blank=True,
        validators=[RegexValidator(r'^[0-9a-zA-Z]{15}$')] # Relaxed to any 15 chars for testing
    )
    bank_account_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    ifsc_code = models.CharField(
        max_length=11, 
        null=True, 
        blank=True,
        validators=[RegexValidator(r'^[A-Z0-9]{11}$')] # Relaxed
    )
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    emp_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    adhar_number = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        unique=True,
        validators=[RegexValidator(r'^\d{12}$', 'Aadhar number must be exactly 12 digits.')]
    )
    
    # Anti-Spam / Ban Status
    ban_until = models.DateTimeField(null=True, blank=True)
    violation_count = models.PositiveIntegerField(default=0)
    
    # Location Preference (for Inspectors)
    preferred_venue = models.ForeignKey('Venue', on_delete=models.SET_NULL, null=True, blank=True, related_name='preferred_inspectors')
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    def save(self, *args, **kwargs):
        if self.role == self.Role.INSPECTOR and not self.emp_id:
            import datetime
            year = datetime.date.today().year
            count = User.objects.filter(role=self.Role.INSPECTOR).count() + 1
            self.emp_id = f"EMP-{year}-{count:04d}"
        super().save(*args, **kwargs)
    @property
    def has_active_subscription(self):
        # As per the new commission-based business model, all users 
        # effectively have an "active subscription" for free unrestricted access.
        return True
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    posts_allowed = models.PositiveIntegerField(default=0)  
    posts_used = models.PositiveIntegerField(default=0)
    def __str__(self):
        return f"{self.user.username} - {self.plan_name} (₹{self.amount})"
class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    class Meta:
        verbose_name_plural = 'Categories'
    def __str__(self):
        return f"{self.parent.name} -> {self.name}" if self.parent else self.name
class VendorProfile(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    categories = models.ManyToManyField(Category, related_name='vendors')
    rating = models.FloatField(default=0.0)
    total_projects_completed = models.IntegerField(default=0)
    verification_status = models.CharField(
        max_length=20, 
        choices=VerificationStatus.choices, 
        default=VerificationStatus.PENDING
    )
    portfolio_url = models.URLField(blank=True, null=True)
    def __str__(self):
        return f"{self.user.username} Profile"

class Venue(models.Model):
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.name
class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    exhibitor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    assigned_vendor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_projects')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='projects')
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    location_custom = models.CharField(max_length=255, blank=True, null=True, help_text="Used if 'Other' is selected")
    venue_details = models.TextField(null=True, blank=True)
    sample_media = models.FileField(upload_to='project_samples/', null=True, blank=True, help_text="Upload sample images, floorplans, or references")
    event_date = models.DateField(null=True, blank=True)
    stall_size = models.CharField(max_length=100, null=True, blank=True)
    preferred_materials = models.TextField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    assigned_site_inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_site_inspections')
    site_inspector_working_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    is_under_failure_review = models.BooleanField(default=False)
    failure_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title
class Proposal(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        RESENT = 'RESENT', 'Resent Quotation'
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='proposals')
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_proposals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    is_resent = models.BooleanField(default=False)
    resent_at = models.DateTimeField(null=True, blank=True)
    original_proposal = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='resent_versions')
    created_at = models.DateTimeField(auto_now_add=True)
    revision_count = models.PositiveIntegerField(default=0)
    
    @property
    def net_payout(self):
        return float(self.amount) * 0.90

    def __str__(self):
        return f"Proposal by {self.vendor.username} for {self.project.title}"

class ProjectMedia(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='additional_media')
    file = models.FileField(upload_to='project_media/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ProposalMedia(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='additional_media')
    file = models.FileField(upload_to='proposal_media/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Milestone(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed Work'
        VERIFIED = 'VERIFIED', 'Verified by Inspector'
        APPROVED = 'APPROVED', 'Approved by Exhibitor'
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    due_date = models.DateField(null=True, blank=True)
    def __str__(self):
        return f"{self.project.title} - {self.title}"
class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Funding'
        HELD = 'HELD', 'Held in Escrow'
        RELEASED = 'RELEASED', 'Released to Vendor'
        REFUNDED = 'REFUNDED', 'Refunded to Exhibitor'
    milestone = models.OneToOneField(Milestone, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"Payment for {self.milestone}"
class Inspection(models.Model):
    class Status(models.TextChoices):
        PASS = 'PASS', 'Pass'
        FAIL = 'FAIL', 'Fail'
        ISSUES_FOUND = 'ISSUES_FOUND', 'Issues Found - Needs Rework'
    inspector = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inspections')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='inspections')
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='inspections', null=True, blank=True)
    report = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices)
    work_submission = models.FileField(upload_to='inspection_work/', blank=True, null=True) 
    is_approved_by_exhibitor = models.BooleanField(default=False)
    vendor_rating = models.PositiveIntegerField(default=0) 
    inspection_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Inspection on {self.project.title} by {self.inspector.username}"
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    is_flagged = models.BooleanField(default=False)
    is_call_link = models.BooleanField(default=False)
    is_group_message = models.BooleanField(default=False)
    call_type = models.CharField(max_length=10, choices=[('AUDIO', 'Audio'), ('VIDEO', 'Video')], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        receiver_name = self.receiver.username if self.receiver else "Group"
        return f"From {self.sender.username} to {receiver_name} (Project: {self.project.title if self.project else 'N/A'})"

class MessageReadStatus(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')

    def __str__(self):
        return f"{self.user.username} read {self.message}"

class Violation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='violations')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Violation by {self.user.username} at {self.created_at}"
class JobPosting(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title
def job_application_upload_path(instance, filename):
    job_title = instance.job.title.replace(" ", "_")
    candidate_name = instance.candidate_name.replace(" ", "_")
    return f'resumes/{job_title}/{candidate_name}/{filename}'
class JobApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        REVIEWING = 'REVIEWING', 'Under Review'
        INTERVIEWING = 'INTERVIEWING', 'Interview Scheduled'
        REJECTED = 'REJECTED', 'Rejected'
        HIRED = 'HIRED', 'Hired'
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    candidate_name = models.CharField(max_length=255)
    candidate_email = models.EmailField()
    resume = models.FileField(upload_to=job_application_upload_path)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.candidate_name} for {self.job.title}"