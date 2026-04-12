from django import forms
from django.contrib.auth.forms import UserCreationForm
from ..models import User

COUNTRY_CODES = [
    ('+91',  '🇮🇳 India (+91)'),
    ('+1',   '🇺🇸 USA (+1)'),
    ('+44',  '🇬🇧 UK (+44)'),
    ('+61',  '🇦🇺 Australia (+61)'),
    ('+971', '🇦🇪 UAE (+971)'),
    ('+65',  '🇸🇬 Singapore (+65)'),
    ('+49',  '🇩🇪 Germany (+49)'),
    ('+33',  '🇫🇷 France (+33)'),
    ('+39',  '🇮🇹 Italy (+39)'),
    ('+34',  '🇪🇸 Spain (+34)'),
    ('+7',   '🇷🇺 Russia (+7)'),
    ('+86',  '🇨🇳 China (+86)'),
    ('+81',  '🇯🇵 Japan (+81)'),
    ('+82',  '🇰🇷 South Korea (+82)'),
    ('+55',  '🇧🇷 Brazil (+55)'),
    ('+52',  '🇲🇽 Mexico (+52)'),
    ('+27',  '🇿🇦 South Africa (+27)'),
    ('+234', '🇳🇬 Nigeria (+234)'),
    ('+20',  '🇪🇬 Egypt (+20)'),
    ('+92',  '🇵🇰 Pakistan (+92)'),
    ('+880', '🇧🇩 Bangladesh (+880)'),
    ('+94',  '🇱🇰 Sri Lanka (+94)'),
    ('+977', '🇳🇵 Nepal (+977)'),
    ('+60',  '🇲🇾 Malaysia (+60)'),
    ('+62',  '🇮🇩 Indonesia (+62)'),
    ('+66',  '🇹🇭 Thailand (+66)'),
    ('+84',  '🇻🇳 Vietnam (+84)'),
    ('+63',  '🇵🇭 Philippines (+63)'),
    ('+98',  '🇮🇷 Iran (+98)'),
    ('+966', '🇸🇦 Saudi Arabia (+966)'),
    ('+974', '🇶🇦 Qatar (+974)'),
    ('+965', '🇰🇼 Kuwait (+965)'),
    ('+973', '🇧🇭 Bahrain (+973)'),
    ('+968', '🇴🇲 Oman (+968)'),
    ('+90',  '🇹🇷 Turkey (+90)'),
    ('+380', '🇺🇦 Ukraine (+380)'),
    ('+48',  '🇵🇱 Poland (+48)'),
    ('+31',  '🇳🇱 Netherlands (+31)'),
    ('+32',  '🇧🇪 Belgium (+32)'),
    ('+41',  '🇨🇭 Switzerland (+41)'),
    ('+43',  '🇦🇹 Austria (+43)'),
    ('+46',  '🇸🇪 Sweden (+46)'),
    ('+47',  '🇳🇴 Norway (+47)'),
    ('+45',  '🇩🇰 Denmark (+45)'),
    ('+358', '🇫🇮 Finland (+358)'),
    ('+64',  '🇳🇿 New Zealand (+64)'),
    ('+1',   '🇨🇦 Canada (+1)'),
    ('+54',  '🇦🇷 Argentina (+54)'),
    ('+56',  '🇨🇱 Chile (+56)'),
    ('+57',  '🇨🇴 Colombia (+57)'),
]

def _country_code_widget():
    return forms.Select(attrs={
        'class': 'form-select rounded-3 country-code-select',
        'id': 'id_country_code',
    })

class CustomUserCreationForm(UserCreationForm):
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODES,
        initial='+91',
        required=True,
        widget=_country_code_widget(),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username', 'email', 'role',
            'phone_number', 'company_name', 'gst_number',
            'bank_account_number', 'ifsc_code', 'bank_name',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [
            (User.Role.EXHIBITOR, 'Exhibitor'),
            (User.Role.VENDOR, 'Vendor'),
        ]
        self.fields['company_name'].required = True
        self.fields['gst_number'].required = True
        self.fields['email'].required = True
        self.fields['email'].widget.attrs.update({
            'class': 'form-control rounded-3',
            'type': 'email',
            'placeholder': 'you@example.com',
            'required': True,
        })
        self.fields['phone_number'].required = True
        self.fields['phone_number'].help_text = 'Enter 10-digit number without country code.'
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-control rounded-3',
            'maxlength': '10',
            'minlength': '10',
            'pattern': r'\d{10}',
            'inputmode': 'numeric',
            'placeholder': '9876543210',
            'title': 'Enter exactly 10 digits',
        })
        for field_name, field in self.fields.items():
            if field_name not in ('country_code', 'email', 'phone_number'):
                field.widget.attrs.update({'class': 'form-control rounded-3'})

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '')
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits.')
        return digits

    def clean(self):
        cleaned_data = super().clean()
        country = cleaned_data.get('country_code', '+91')
        phone = cleaned_data.get('phone_number', '')
        if country and phone:
            full_number = f"{country}{phone}"
            if User.objects.filter(phone_number=full_number).exists():
                self.add_error('phone_number', 'This phone number is already registered.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        country = self.cleaned_data.get('country_code', '+91')
        phone = self.cleaned_data.get('phone_number', '')
        user.phone_number = f"{country}{phone}"
        if commit:
            user.save()
        return user


class SiteInspectorCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}), required=True)
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODES,
        initial='+91',
        required=True,
        widget=_country_code_widget(),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'adhar_number', 'preferred_venue', 'profile_picture', 'password')
        widgets = {
            'preferred_venue': forms.Select(attrs={'class': 'form-select rounded-3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['email'].widget.attrs.update({
            'class': 'form-control rounded-3',
            'type': 'email',
            'placeholder': 'inspector@example.com',
        })
        self.fields['phone_number'].required = True
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-control rounded-3',
            'maxlength': '10',
            'minlength': '10',
            'pattern': r'\d{10}',
            'inputmode': 'numeric',
            'placeholder': '9876543210',
            'title': 'Enter exactly 10 digits',
        })
        self.fields['adhar_number'].widget.attrs.update({
            'class': 'form-control rounded-3',
            'maxlength': '12',
            'minlength': '12',
            'pattern': r'\d{12}',
            'inputmode': 'numeric',
            'placeholder': '123456789012',
            'title': 'Aadhar must be exactly 12 digits',
        })
        for field_name, field in self.fields.items():
            if field_name not in ('country_code', 'email', 'phone_number', 'adhar_number', 'password'):
                field.widget.attrs.update({'class': 'form-control rounded-3'})

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '')
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits.')
        return digits

    def clean_adhar_number(self):
        adhar = self.cleaned_data.get('adhar_number', '')
        if adhar:
            digits = ''.join(filter(str.isdigit, adhar))
            if len(digits) != 12:
                raise forms.ValidationError('Aadhar number must be exactly 12 digits.')
            return digits
        return adhar

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = User.Role.INSPECTOR
        country = self.cleaned_data.get('country_code', '+91')
        phone = self.cleaned_data.get('phone_number', '')
        user.phone_number = f"{country}{phone}"
        if commit:
            user.save()
        return user


class AdminCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}), required=True)
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODES,
        initial='+91',
        required=False,          # Optional — template may or may not include it
        widget=_country_code_widget(),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['email'].widget.attrs.update({
            'class': 'form-control rounded-3',
            'type': 'email',
            'placeholder': 'admin@example.com',
        })
        self.fields['phone_number'].required = False   # Optional for admins
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-control rounded-3',
            'maxlength': '10',
            'minlength': '10',
            'pattern': r'\d{10}',
            'inputmode': 'numeric',
            'placeholder': '9876543210',
            'title': 'Enter exactly 10 digits',
        })
        for field_name, field in self.fields.items():
            if field_name not in ('country_code', 'email', 'phone_number', 'password'):
                field.widget.attrs.update({'class': 'form-control rounded-3'})

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '')
        if not phone:  # Optional — skip validation if not provided
            return None
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits.')
        return digits

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = User.Role.ADMIN
        user.is_staff = True
        country = self.cleaned_data.get('country_code') or '+91'
        phone = self.cleaned_data.get('phone_number') or ''
        # Only store phone if a number was actually provided
        user.phone_number = f"{country}{phone}" if phone else None
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'email', 'first_name', 'last_name', 'phone_number',
            'company_name', 'gst_number', 'bank_account_number',
            'ifsc_code', 'bank_name', 'profile_picture', 'adhar_number',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control rounded-3', 'type': 'email'})
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-control rounded-3',
            'maxlength': '15',
            'placeholder': '+919876543210',
        })
        if 'adhar_number' in self.fields:
            self.fields['adhar_number'].widget.attrs.update({
                'class': 'form-control rounded-3',
                'maxlength': '12',
                'minlength': '12',
                'pattern': r'\d{12}',
                'inputmode': 'numeric',
                'placeholder': '123456789012',
            })
        for field_name, field in self.fields.items():
            if field_name not in ('email', 'phone_number', 'adhar_number'):
                field.widget.attrs.update({'class': 'form-control rounded-3'})
