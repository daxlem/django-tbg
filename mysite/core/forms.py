from django import forms
from django.forms import ClearableFileInput

from .models import Cinema

class CinemaForm(forms.ModelForm):
    class Meta:
        model = Cinema
        fields = ('id', 'csv')
        widgets = {
            'csv' : ClearableFileInput(attrs={'multiple': True, 'accept': ".xlsx, .xls, .csv", 'class': 'custom-select', 'webkitdirectory': True, 'directory': True}),
        }
        
