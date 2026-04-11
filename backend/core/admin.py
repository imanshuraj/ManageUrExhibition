from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Category, VendorProfile, Project, Proposal, 
    Milestone, Payment, Inspection, Message, Violation
)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone_number', 'company_name', 'is_verified', 'profile_picture')}),
    )
    list_display = ('username', 'email', 'role', 'is_verified', 'is_staff', 'profile_picture_preview')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser')
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            from django.utils.html import format_html
            return format_html('<img src="{}" width="30" height="30" style="border-radius: 50%;" />', obj.profile_picture.url)
        return "-"
    profile_picture_preview.short_description = "Pic"
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name',)
@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification_status', 'rating', 'total_projects_completed')
    list_filter = ('verification_status',)
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('categories',)
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'exhibitor', 'status', 'location', 'assigned_site_inspector', 'budget_min', 'budget_max')
    list_filter = ('status', 'category', 'location', 'assigned_site_inspector')
    search_fields = ('title', 'exhibitor__username')
@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('project', 'vendor', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('project__title', 'vendor__username')
@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'amount', 'status', 'due_date')
    list_filter = ('status',)
    search_fields = ('title', 'project__title')
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('milestone', 'amount', 'status', 'created_at', 'released_at')
    list_filter = ('status',)
@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('project', 'inspector', 'status', 'vendor_rating', 'inspection_date')
    list_filter = ('status', 'vendor_rating')
    search_fields = ('project__title', 'inspector__username')
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'project', 'is_flagged', 'created_at')
    list_filter = ('is_flagged',)
    search_fields = ('sender__username', 'receiver__username', 'content')
@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username', 'description')