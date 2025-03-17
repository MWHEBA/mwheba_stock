from django import forms
from django.utils.translation import gettext_lazy as _
from .models import User

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        labels = {
            'first_name': _('الاسم الأول'),
            'last_name': _('الاسم الأخير'),
            'email': _('البريد الإلكتروني'),
            'phone_number': _('رقم الهاتف'),
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
        }
