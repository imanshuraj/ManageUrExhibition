from django import forms
from ..models import Inspection

class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = ('status', 'vendor_rating', 'report', 'work_submission')
        widgets = {
            'report': forms.Textarea(attrs={'rows': 4}),
            'vendor_rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'placeholder': 'Rate 1-5'}),
        }
