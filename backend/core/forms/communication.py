from django import forms
from ..models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('content', 'image', 'file')
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type your message here...', 'autocomplete': 'off'}),
            'image': forms.FileInput(attrs={'class': 'd-none', 'id': 'chat-image-input', 'accept': 'image/*'}),
            'file': forms.FileInput(attrs={'class': 'd-none', 'id': 'chat-file-input'}),
        }
