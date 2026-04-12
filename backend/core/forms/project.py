from django import forms
from ..models import Category, VendorProfile, Project, Proposal, Milestone, Venue

class VendorProfileForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), widget=forms.CheckboxSelectMultiple, required=True)
    class Meta:
        model = VendorProfile
        fields = ('categories', 'portfolio_url')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['portfolio_url'].widget.attrs.update({'class': 'form-control rounded-3'})

class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

class ProjectForm(forms.ModelForm):
    additional_media_files = forms.FileField(widget=MultipleFileInput(attrs={'multiple': True, 'class': 'form-control rounded-3'}), required=False, help_text="Upload up to 10 additional reference files/images.")
    class Meta:
        model = Project
        fields = ('title', 'category', 'venue', 'location_custom', 'venue_details', 'event_date',
                  'stall_size', 'preferred_materials', 'description', 'budget_min', 'budget_max', 'deadline', 'sample_media')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Stall Fabrication – Tech Summit 2026, Pragati Maidan'}),
            'venue': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'location_custom': forms.TextInput(attrs={'placeholder': 'If Other, specify Venue/City', 'class': 'form-control rounded-3'}),
            'venue_details': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g. Hall 8, Stall No. B-24, Ground Floor, Gate 3'}),
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'stall_size': forms.TextInput(attrs={'placeholder': 'e.g. 3m x 3m (9 sqm), Corner Stall'}),
            'preferred_materials': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. Aluminium frame, fabric graphics, LED lighting, eco-friendly materials...'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the exact work required, your branding guidelines, design references, etc.'}),
            'budget_min': forms.NumberInput(attrs={'placeholder': 'e.g. 25000'}),
            'budget_max': forms.NumberInput(attrs={'placeholder': 'e.g. 75000'}),
        }

class ProposalForm(forms.ModelForm):
    additional_media_files = forms.FileField(widget=MultipleFileInput(attrs={'multiple': True, 'class': 'form-control rounded-3'}), required=False, help_text="Upload up to 10 additional reference files.")
    class Meta:
        model = Proposal
        fields = ('amount', 'description')

class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ('title', 'description', 'amount', 'due_date')
        widgets = {'due_date': forms.DateInput(attrs={'type': 'date'})}
