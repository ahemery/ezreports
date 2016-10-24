from django import forms
from django.conf import settings
from django.core.validators import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *


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


class LienForm(forms.ModelForm):

    class Meta:
        model = Lien
        fields = ['ressource', 'disabled', 'slug']
        widgets = {
            'ressource': forms.Select(attrs={
                'class': 'form-control',

            }),
            'disabled': forms.CheckboxInput(
                attrs={'class': ''},
            ),
            'slug': forms.HiddenInput()
        }
        labels = {
            'ressource': 'Ressource',
            'disabled': 'Désactivé ?',
        },



