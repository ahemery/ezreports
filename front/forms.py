from django import forms
from django.conf import settings
from django.core.validators import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField(required=True,
                               min_length=4,
                               max_length=64,
                               widget=forms.TextInput(attrs={
                                   'class': 'form-control',
                                   'placeholder': 'Identifiant...',
                               }))
    password = forms.CharField(required=True,
                               min_length=4,
                               max_length=16,
                               widget=forms.PasswordInput(attrs={
                                   'class': 'form-control',
                                   'placeholder': 'Mot de passe...',
                               }))

    def clean(self):
        return self.cleaned_data
